import motor.motor_asyncio
from datetime import datetime, timedelta
from config import config
from typing import Dict, Any, List, Optional
from loguru import logger

class LastPerson07_Database:
    """Production MongoDB handler"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    async def LastPerson07_connect(self):
        """Connect to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.db = self.client.bannerbot
            await self.db.command("ping")
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def LastPerson07_ping(self) -> bool:
        """Ping database"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            await self.db.command("ping")
            return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False
    
    async def LastPerson07_init_indexes(self):
        """Create database indexes"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            users = self.db.users
            bans = self.db.bans
            logs = self.db.logs
            
            # Create indexes
            await users.create_index("user_id", unique=True)
            await bans.create_index("user_id", unique=True)
            await logs.create_index("timestamp", expireAfterSeconds=2592000)
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def LastPerson07_get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            user = await self.db.users.find_one({"user_id": user_id})
            if user:
                user['is_admin'] = user_id in config.ADMIN_IDS
            return user
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    async def LastPerson07_upsert_user(
        self,
        user_id: int,
        username: str = "",
        first_name: str = ""
    ):
        """Create or update user"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "username": username or "unknown",
                    "first_name": first_name or "User",
                    "last_active": datetime.utcnow()
                }, "$setOnInsert": {
                    "banners_generated": 0,
                    "created_at": datetime.utcnow(),
                    "daily_banners": 0
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Upsert user error: {e}")
    
    async def LastPerson07_increment_banners(self, user_id: int):
        """Increment user banner count"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            now = datetime.utcnow()
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"banners_generated": 1, "daily_banners": 1},
                    "$set": {"last_active": now}
                }
            )
        except Exception as e:
            logger.error(f"Increment error: {e}")
    
    async def LastPerson07_is_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            ban = await self.db.bans.find_one({"user_id": user_id})
            return ban is not None
        except Exception as e:
            logger.error(f"Ban check error: {e}")
            return False
    
    async def LastPerson07_ban_user(
        self,
        user_id: int,
        admin_id: int,
        reason: str = "Admin ban"
    ):
        """Ban a user"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            await self.db.bans.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "admin_id": admin_id,
                    "reason": reason,
                    "banned_at": datetime.utcnow()
                }},
                upsert=True
            )
            await self.LastPerson07_log_action(
                admin_id,
                "ban_user",
                f"Banned user {user_id}. Reason: {reason}"
            )
            logger.info(f"✅ User {user_id} banned")
        except Exception as e:
            logger.error(f"Ban error: {e}")
    
    async def LastPerson07_unban_user(self, user_id: int):
        """Unban a user"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            await self.db.bans.delete_one({"user_id": user_id})
            logger.info(f"✅ User {user_id} unbanned")
        except Exception as e:
            logger.error(f"Unban error: {e}")
    
    async def LastPerson07_log_action(
        self,
        user_id: int,
        action: str,
        details: str = ""
    ):
        """Log user action"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            await self.db.logs.insert_one({
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Log error: {e}")
    
    async def LastPerson07_get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            total_users = await self.db.users.count_documents({})
            total_banners = 0
            active_24h = 0
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            async for user in self.db.users.find({}):
                total_banners += user.get("banners_generated", 0)
                if user.get("last_active", datetime.min) > cutoff_time:
                    active_24h += 1
            
            return {
                "total_users": total_users,
                "total_banners": total_banners,
                "active_24h": active_24h
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"total_users": 0, "total_banners": 0, "active_24h": 0}
    
    async def LastPerson07_get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get top banner creators"""
        try:
            if not self.db:
                await self.LastPerson07_connect()
            
            pipeline = [
                {"$sort": {"banners_generated": -1}},
                {"$limit": limit},
                {"$project": {"user_id": 1, "username": 1, "banners_generated": 1}}
            ]
            return await self.db.users.aggregate(pipeline).to_list(limit)
        except Exception as e:
            logger.error(f"Top users error: {e}")
            return []

# Global instance
db = LastPerson07_Database()
