import motor.motor_asyncio
from datetime import datetime, timedelta
from config import config
from typing import Dict, Any, List, Optional
from loguru import logger


class Database:
    """
    Production MongoDB Manager
    Designed for high-concurrency async bots
    """

    def __init__(self):
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db = None

    # ---------------- CONNECT ---------------- #

    async def connect(self):
        """Create Mongo connection ONCE"""
        if self.client is not None:
            return

        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.MONGO_URI,
                maxPoolSize=50,   # 🔥 important for bots
                minPoolSize=5,
                serverSelectionTimeoutMS=5000
            )

            self.db = self.client["bannerbot"]

            # Test connection
            await self.client.admin.command("ping")

            logger.info("✅ MongoDB connected")

            await self.init_indexes()

        except Exception as e:
            logger.exception(f"❌ Mongo connection failed: {e}")
            raise

    # ---------------- INTERNAL ---------------- #

    async def _ensure_connected(self):
        """
        NEVER check `if self.db`
        Always use explicit None comparison
        """
        if self.client is None:
            await self.connect()

    # ---------------- INDEXES ---------------- #

    async def init_indexes(self):
        """Create indexes once"""
        try:
            users = self.db.users
            bans = self.db.bans
            logs = self.db.logs

            await users.create_index("user_id", unique=True)
            await users.create_index("last_active")

            await bans.create_index("user_id", unique=True)

            # Auto-delete logs after 30 days
            await logs.create_index(
                "timestamp",
                expireAfterSeconds=60 * 60 * 24 * 30
            )

            logger.info("✅ Mongo indexes ready")

        except Exception as e:
            logger.warning(f"Index warning: {e}")

    # ---------------- USERS ---------------- #

    async def get_user(self, user_id: int) -> Optional[Dict]:
        await self._ensure_connected()

        user = await self.db.users.find_one({"user_id": user_id})

        if user:
            user["is_admin"] = user_id in config.ADMIN_IDS

        return user

    async def upsert_user(
        self,
        user_id: int,
        username: str = "",
        first_name: str = ""
    ):
        await self._ensure_connected()

        await self.db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "username": username or "unknown",
                    "first_name": first_name or "User",
                    "last_active": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow(),
                    "banners_generated": 0,
                    "daily_banners": 0
                }
            },
            upsert=True
        )

    async def increment_banners(self, user_id: int):
        await self._ensure_connected()

        await self.db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "banners_generated": 1,
                    "daily_banners": 1
                },
                "$set": {"last_active": datetime.utcnow()}
            }
        )

    # ---------------- BANS ---------------- #

    async def is_banned(self, user_id: int) -> bool:
        await self._ensure_connected()

        ban = await self.db.bans.find_one({"user_id": user_id})
        return ban is not None

    async def ban_user(
        self,
        user_id: int,
        admin_id: int,
        reason: str = "Admin ban"
    ):
        await self._ensure_connected()

        await self.db.bans.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "admin_id": admin_id,
                    "reason": reason,
                    "banned_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        await self.log_action(
            admin_id,
            "ban_user",
            f"Banned {user_id} | {reason}"
        )

        logger.info(f"✅ User banned: {user_id}")

    async def unban_user(self, user_id: int):
        await self._ensure_connected()

        await self.db.bans.delete_one({"user_id": user_id})
        logger.info(f"✅ User unbanned: {user_id}")

    # ---------------- LOGS ---------------- #

    async def log_action(
        self,
        user_id: int,
        action: str,
        details: str = ""
    ):
        await self._ensure_connected()

        await self.db.logs.insert_one({
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow()
        })

    # ---------------- STATS ---------------- #

    async def get_stats(self) -> Dict[str, Any]:
        await self._ensure_connected()

        cutoff = datetime.utcnow() - timedelta(hours=24)

        total_users = await self.db.users.count_documents({})

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_banners": {"$sum": "$banners_generated"}
                }
            }
        ]

        result = await self.db.users.aggregate(pipeline).to_list(1)

        total_banners = result[0]["total_banners"] if result else 0

        active_24h = await self.db.users.count_documents({
            "last_active": {"$gte": cutoff}
        })

        return {
            "total_users": total_users,
            "total_banners": total_banners,
            "active_24h": active_24h
        }

    # ---------------- TOP USERS ---------------- #

    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        await self._ensure_connected()

        cursor = self.db.users.find(
            {},
            {"user_id": 1, "username": 1, "banners_generated": 1}
        ).sort("banners_generated", -1).limit(limit)

        return await cursor.to_list(limit)


# 🔥 SINGLE GLOBAL INSTANCE
db = Database()
