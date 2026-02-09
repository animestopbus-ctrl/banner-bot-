from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from database.mongo import db
from loguru import logger

class LastPerson07_AuthMiddleware(BaseMiddleware):
    """Authorization & ban checking middleware"""
    
    async def __call__(self, handler, event: Update, data):
        try:
            # Extract user ID
            user_id = None
            if isinstance(event, Message):
                user_id = event.from_user.id
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
            
            if not user_id:
                return await handler(event, data)
            
            # Check ban
            is_banned = await db.LastPerson07_is_banned(user_id)
            if is_banned:
                if isinstance(event, Message):
                    await event.answer("❌ You are banned from this bot.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ You are banned from using this bot.", show_alert=True)
                logger.warning(f"Banned user {user_id} attempted action")
                return
            
            # Track user
            username = event.from_user.username or ""
            first_name = event.from_user.first_name or "User"
            await db.LastPerson07_upsert_user(user_id, username, first_name)
            
            # Log action
            action = "message" if isinstance(event, Message) else "callback"
            await db.LastPerson07_log_action(user_id, action)
            
            # Pass to handler
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            return await handler(event, data)
