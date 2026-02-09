import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger

from config import config
from database.mongo import db
from middlewares.auth import LastPerson07_AuthMiddleware
from handlers import start, banner, admin

# Setup loguru
logger.remove()
logger.add(
    config.LOGS_DIR / "bot.log",
    rotation="1 MB",
    retention="7 days",
    level="INFO"
)
logger.add(sys.stdout, level="INFO")

# Bot & Dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def LastPerson07_setup_commands():
    """Setup bot commands menu"""
    try:
        commands = [
            BotCommand(command="start", description="🚀 Start the bot"),
            BotCommand(command="create", description="🎨 Create banner"),
            BotCommand(command="stats", description="📊 View stats"),
            BotCommand(command="help", description="❓ Help"),
            BotCommand(command="admin", description="🔨 Admin panel (admin only)"),
        ]
        await bot.set_my_commands(commands)
        logger.info("✅ Commands set successfully")
    except Exception as e:
        logger.error(f"Command setup error: {e}")

async def LastPerson07_init_bot():
    """Initialize bot"""
    try:
        logger.info("🔄 Initializing bot...")
        
        # Init DB
        await db.LastPerson07_connect()
        await db.LastPerson07_init_indexes()
        logger.info("✅ Database initialized")
        
        # Setup commands
        await LastPerson07_setup_commands()
        
        # Register middlewares
        dp.message.middleware(LastPerson07_AuthMiddleware())
        dp.callback_query.middleware(LastPerson07_AuthMiddleware())
        logger.info("✅ Middlewares registered")
        
        # Register routers
        dp.include_router(start.router)
        dp.include_router(banner.router)
        dp.include_router(admin.router)
        logger.info("✅ Routers registered")
        
        return True
    except Exception as e:
        logger.error(f"❌ Bot init error: {e}", exc_info=True)
        return False

async def LastPerson07_start_bot_safe():
    """Start bot with error handling"""
    try:
        if not await LastPerson07_init_bot():
            logger.error("❌ Bot initialization failed")
            return
        
        logger.info("🚀 Bot polling started...")
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )
        
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}", exc_info=True)
        await asyncio.sleep(5)
        # Restart
        await LastPerson07_start_bot_safe()

if __name__ == "__main__":
    try:
        asyncio.run(LastPerson07_start_bot_safe())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
