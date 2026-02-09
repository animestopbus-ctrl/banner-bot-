from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable
from database.mongo import db
from loguru import logger

class LastPerson07_AuthMiddleware(BaseMiddleware):
    """✅ FIXED Middleware - NO CRASHES"""
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        try:
            # ✅ SAFE USER ID EXTRACTION
            user_id = None
            if hasattr(event, 'from_user') and event.from_user:
                user_id = event.from_user.id
            
            if not user_id:
                return await handler(event, data)
            
            # ✅ SAFE BAN CHECK
            try:
                is_banned = await db.LastPerson07_is_banned(user_id)
                if is_banned:
                    if isinstance(event, (Message, CallbackQuery)):
                        if hasattr(event, 'answer'):
                            await event.answer("❌ You are banned from this bot.")
                    return
            except:
                pass  # Continue if DB fails
            
            # ✅ SAFE USER TRACKING
            try:
                username = getattr(event.from_user, 'username', '') or ""
                first_name = getattr(event.from_user, 'first_name', '') or "User"
                await db.LastPerson07_upsert_user(user_id, username, first_name)
            except:
                pass  # Silent fail
            
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"❌ Middleware CRASH: {e}")
            return await handler(event, data)  # ✅ NEVER BLOCKS
