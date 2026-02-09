# database/mongo.py

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger

from config import config


class Database:
    """
    🚀 Production MongoDB Manager

    ✔ Safe async connection
    ✔ No boolean DB checks
    ✔ Connection lock
    ✔ Retry support
    ✔ Optimized pooling
    ✔ Container safe
    """

    def __init__(self):

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

        self._connect_lock = asyncio.Lock()
        self._indexes_ready = False

    # =====================================================
    # CONNECTION
    # =====================================================

    async def connect(self) -> None:
        """
        Idempotent Mongo connection.
        Safe against race conditions.
        """

        if self.client is not None:
            return

        async with self._connect_lock:

            if self.client is not None:
                return

            retries = 3

            for attempt in range(retries):
                try:
                    self.client = motor.motor_asyncio.AsyncIOMotorClient(
                        config.MONGO_URI,
                        maxPoolSize=100,      # better concurrency
                        minPoolSize=5,
                        serverSelectionTimeoutMS=5000,
                        socketTimeoutMS=20000
                    )

                    db_name = getattr(config, "MONGO_DB_NAME", "bannerbot")

                    self.db = self.client[db_name]

                    await self.client.admin.command("ping")

                    logger.info("✅ MongoDB connected")

                    await self.init_indexes()

                    return

                except Exception as e:

                    logger.warning(
                        f"Mongo connect failed (attempt {attempt+1}/{retries}): {e}"
                    )

                    await asyncio.sleep(2)

            raise RuntimeError("❌ Could not connect to MongoDB")

    async def close(self):

        if self.client is None:
            return

        try:
            self.client.close()
            logger.info("✅ MongoDB closed")

        finally:
            self.client = None
            self.db = None
            self._indexes_ready = False

    async def ping(self) -> bool:

        try:
            if self.client is None:
                await self.connect()

            await self.client.admin.command("ping")

            return True

        except Exception as e:
            logger.warning(f"Mongo ping failed: {e}")
            return False

    async def _ensure(self):

        if self.client is None:
            await self.connect()

        if self.db is None:
            raise RuntimeError("Mongo DB not initialized")

    # =====================================================
    # INDEXES
    # =====================================================

    async def init_indexes(self):

        if self._indexes_ready:
            return

        async with self._connect_lock:

            if self._indexes_ready:
                return

            try:

                users = self.db.users
                bans = self.db.bans
                logs = self.db.logs

                await users.create_index(
                    "user_id",
                    unique=True,
                    background=True
                )

                await users.create_index(
                    "last_active",
                    background=True
                )

                await bans.create_index(
                    "user_id",
                    unique=True,
                    background=True
                )

                await logs.create_index(
                    "timestamp",
                    expireAfterSeconds=60 * 60 * 24 * 30
                )

                self._indexes_ready = True

                logger.info("✅ Mongo indexes ready")

            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

    # =====================================================
    # USERS
    # =====================================================

    async def get_user(self, user_id: int) -> Optional[Dict]:

        await self._ensure()

        try:

            user = await self.db.users.find_one({"user_id": user_id})

            if user:
                user["is_admin"] = user_id in getattr(config, "ADMIN_IDS", [])

            return user

        except Exception as e:
            logger.exception(f"Get user error: {e}")
            return None

    async def upsert_user(self, user_id: int, username="", first_name=""):

        await self._ensure()

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
            logger.exception(f"Upsert error: {e}")

    async def increment_banners(self, user_id: int, inc: int = 1):

        await self._ensure()

        try:

            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {
                        "banners_generated": inc,
                        "daily_banners": inc
                    },
                    "$set": {"last_active": datetime.utcnow()}
                }
            )

        except Exception as e:
            logger.exception(f"Increment error: {e}")

    # =====================================================
    # BANS
    # =====================================================

    async def is_banned(self, user_id: int) -> bool:

        await self._ensure()

        try:

            ban = await self.db.bans.find_one({"user_id": user_id})

            return ban is not None

        except Exception as e:
            logger.exception(f"Ban check error: {e}")
            return False

    async def ban_user(self, user_id: int, admin_id: int, reason="Admin ban"):

        await self._ensure()

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

            await self.log_action(admin_id, "ban_user", f"{user_id} | {reason}")

            logger.info(f"✅ User banned: {user_id}")

        except Exception as e:
            logger.exception(f"Ban error: {e}")

    async def unban_user(self, user_id: int):

        await self._ensure()

        try:
            await self.db.bans.delete_one({"user_id": user_id})
        except Exception as e:
            logger.exception(f"Unban error: {e}")

    # =====================================================
    # LOGS
    # =====================================================

    async def log_action(self, user_id: int, action: str, details=""):

        await self._ensure()

        try:

            await self.db.logs.insert_one({
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            })

        except Exception as e:
            logger.exception(f"Log error: {e}")

    # =====================================================
    # STATS
    # =====================================================

    async def get_stats(self) -> Dict[str, Any]:

        await self._ensure()

        try:

            cutoff = datetime.utcnow() - timedelta(hours=24)

            total_users = await self.db.users.estimated_document_count()

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

        except Exception as e:
            logger.exception(f"Stats error: {e}")
            return {"total_users": 0, "total_banners": 0, "active_24h": 0}

    # =====================================================
    # TOP USERS
    # =====================================================

    async def get_top_users(self, limit: int = 10) -> List[Dict]:

        await self._ensure()

        try:

            cursor = self.db.users.find(
                {},
                {"user_id": 1, "username": 1, "banners_generated": 1}
            ).sort("banners_generated", -1).limit(limit)

            return await cursor.to_list(limit)

        except Exception as e:
            logger.exception(f"Top users error: {e}")
            return []


# ⭐ SINGLE GLOBAL INSTANCE
db = Database()
