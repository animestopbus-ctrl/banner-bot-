from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from config import config
from database.mongo import db
from loguru import logger

router = Router()

@router.message(Command("admin"))
async def LastPerson07_admin_panel(message: Message):
    """Admin panel"""
    try:
        if message.from_user.id not in config.ADMIN_IDS:
            await message.answer("🔒 Admin only")
            return
        
        stats = await db.LastPerson07_get_stats()
        
        text = f"""
🔨 **ADMIN PANEL - LastPerson07**

📊 **Bot Statistics:**
• Total Users: {stats['total_users']}
• Total Banners: {stats['total_banners']:,}
• Active 24h: {stats['active_24h']}

**Available Commands:**
/ban_user <user_id> - Ban a user
/unban_user <user_id> - Unban a user
/logs - View recent logs
/search_user <username> - Search user

**Example:**
/ban_user 123456789
        """
        
        await message.answer(text, parse_mode="Markdown")
        logger.info(f"Admin {message.from_user.id} accessed admin panel")
        
    except Exception as e:
        logger.error(f"Admin panel error: {e}")
        await message.answer("❌ Error accessing admin panel")

@router.message(Command("ban_user"))
async def LastPerson07_ban(message: Message):
    """Ban user command"""
    try:
        if message.from_user.id not in config.ADMIN_IDS:
            await message.answer("🔒 Admin only")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Usage: /ban_user <user_id>")
            return
        
        try:
            user_id = int(parts[1])
        except ValueError:
            await message.answer("❌ Invalid user ID")
            return
        
        reason = " ".join(parts[2:]) if len(parts) > 2 else "Admin ban"
        
        await db.LastPerson07_ban_user(user_id, message.from_user.id, reason)
        await message.answer(f"✅ User {user_id} has been banned.\n\nReason: {reason}")
        logger.info(f"Admin {message.from_user.id} banned user {user_id}")
        
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await message.answer("❌ Error banning user")

@router.message(Command("unban_user"))
async def LastPerson07_unban(message: Message):
    """Unban user command"""
    try:
        if message.from_user.id not in config.ADMIN_IDS:
            await message.answer("🔒 Admin only")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Usage: /unban_user <user_id>")
            return
        
        try:
            user_id = int(parts[1])
        except ValueError:
            await message.answer("❌ Invalid user ID")
            return
        
        await db.LastPerson07_unban_user(user_id)
        await message.answer(f"✅ User {user_id} has been unbanned.")
        logger.info(f"Admin {message.from_user.id} unbanned user {user_id}")
        
    except Exception as e:
        logger.error(f"Unban error: {e}")
        await message.answer("❌ Error unbanning user")

@router.message(Command("logs"))
async def LastPerson07_view_logs(message: Message):
    """View recent logs"""
    try:
        if message.from_user.id not in config.ADMIN_IDS:
            await message.answer("🔒 Admin only")
            return
        
        text = """
📋 **Recent Logs**

Logs are stored in MongoDB with 30-day TTL.
Check the logs file: `logs/bot.log`

Commands:
/ban_user - View ban logs
/admin - See all statistics
        """
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Logs error: {e}")
        await message.answer("❌ Error retrieving logs")
