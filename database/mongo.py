# database/mongo.py
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timedelta
from config import config
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio


class Database:
    """
    Production MongoDB Manager
    - call `await db.connect()` on app startup
    - call `await db.close()` on shutdown
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._indexes_ready = False
        self._lock = asyncio.Lock()

    # ---------------- CONNECT / CLOSE ---------------- #

    async def connect(self) -> None:
        """Create Mongo connection ONCE (idempotent)."""
        if self.client is not None:
            return

        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.MONGO_URI,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[config.MONGO_DB_NAME or "bannerbot"]

            # quick ping to ensure connection
            await self.client.admin.command("ping")
            logger.info("✅ MongoDB connected")

            # initialize indexes once
            await self.init_indexes()

        except Exception as e:
            logger.exception(f"❌ Mongo connection failed: {e}")
            # ensure partially created client is closed
            await self.close()
            raise

    async def close(self) -> None:
        """Close client connection (idempotent)."""
        if self.client is None:
            return
        try:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
        except Exception as e:
            logger.warning(f"Error closing Mongo client: {e}")
        finally:
            self.client = None
            self.db = None
            self._indexes_ready = False

    async def ping(self) -> bool:
        """Return True if DB responds to ping."""
        try:
            if self.client is None:
                await self.connect()
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.warning(f"Mongo ping failed: {e}")
            return False

    # ---------------- INTERNAL ---------------- #

    async def _ensure_connected(self) -> None:
        """Helper to guarantee connection before any operation."""
        if self.client is None:
            await self.connect()

    # ---------------- INDEXES ---------------- #

    async def init_indexes(self) -> None:
        """
        Create required indexes. Protected by a lock to avoid races
        when multiple startup coroutines call this concurrently.
        """
        # quick fast-path
        if self._indexes_ready:
            return

        async with self._lock:
            if self._indexes_ready:
                return

            try:
                users = self.db.users
                bans = self.db.bans
                logs = self.db.logs

                # users: unique and last_active for queries
                await users.create_index("user_id", unique=True, background=True)
                await users.create_index("last_active", background=True)

                # bans: unique user_id
                await bans.create_index("user_id", unique=True, background=True)

                # logs: TTL index to auto-delete after 30 days
                await logs.create_index("timestamp", expireAfterSeconds=60 * 60 * 24 * 30, background=True)

                self._indexes_ready = True
                logger.info("✅ Mongo indexes created/verified")

            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

    # ---------------- USERS ---------------- #

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        await self._ensure_connected()
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            if user:
                user["is_admin"] = user_id in getattr(config, "ADMIN_IDS", [])
            return user
        except Exception as e:
            logger.exception(f"Get user error: {e}")
            return None

    async def upsert_user(
        self,
        user_id: int,
        username: str = "",
        first_name: str = ""
    ) -> None:
        """
        Upsert a user record. Guarantees fields exist on insert.
        Uses $setOnInsert to populate defaults.
        """
        await self._ensure_connected()
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username or "unknown",
                        "first_name": first_name or "User",
                        "last_active": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "created_at": datetime.utcnow(),
                        "banners_generated": 0,
                        "daily_banners": 0
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.exception(f"Upsert user error: {e}")

    async def increment_banners(self, user_id: int, inc: int = 1) -> None:
        """Increment banner counters for a user."""
        await self._ensure_connected()
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"banners_generated": inc, "daily_banners": inc},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
        except Exception as e:
            logger.exception(f"Increment banners error: {e}")

    # ---------------- BANS ---------------- #

    async def is_banned(self, user_id: int) -> bool:
        await self._ensure_connected()
        try:
            ban = await self.db.bans.find_one({"user_id": user_id})
            return ban is not None
        except Exception as e:
            logger.exception(f"Ban check error: {e}")
            return False

    async def ban_user(self, user_id: int, admin_id: int, reason: str = "Admin ban") -> None:
        await self._ensure_connected()
        try:
            await self.db.bans.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "admin_id": admin_id,
                        "reason": reason,
                        "banned_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            await self.log_action(admin_id, "ban_user", f"Banned {user_id} | {reason}")
            logger.info(f"✅ User banned: {user_id}")
        except Exception as e:
            logger.exception(f"Ban user error: {e}")

    async def unban_user(self, user_id: int) -> None:
        await self._ensure_connected()
        try:
            await self.db.bans.delete_one({"user_id": user_id})
            logger.info(f"✅ User unbanned: {user_id}")
        except Exception as e:
            logger.exception(f"Unban error: {e}")

    # ---------------- LOGS ---------------- #

    async def log_action(self, user_id: int, action: str, details: str = "") -> None:
        await self._ensure_connected()
        try:
            await self.db.logs.insert_one({
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logger.exception(f"Log action error: {e}")

    # ---------------- STATS ---------------- #

    async def get_stats(self) -> Dict[str, Any]:
        """
        Return aggregated stats:
        - total_users
        - total_banners (aggregation)
        - active_24h
        """
        await self._ensure_connected()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=24)

            total_users = await self.db.users.count_documents({})

            pipeline = [
                {"$group": {"_id": None, "total_banners": {"$sum": "$banners_generated"}}}
            ]
            result = await self.db.users.aggregate(pipeline).to_list(length=1)
            total_banners = int(result[0]["total_banners"]) if result else 0

            active_24h = await self.db.users.count_documents({"last_active": {"$gte": cutoff}})

            return {
                "total_users": total_users,
                "total_banners": total_banners,
                "active_24h": active_24h
            }
        except Exception as e:
            logger.exception(f"Stats error: {e}")
            return {"total_users": 0, "total_banners": 0, "active_24h": 0}

    # ---------------- TOP USERS ---------------- #

    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        await self._ensure_connected()
        try:
            cursor = self.db.users.find(
                {},
                {"user_id": 1, "username": 1, "banners_generated": 1}
            ).sort("banners_generated", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.exception(f"Top users error: {e}")
            return []


# SINGLE GLOBAL INSTANCE
db = Database()
