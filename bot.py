import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger

from config import config
from database.mongo import db
from middlewares.auth import LastPerson07_AuthMiddleware
from handlers import start, banner, admin  # ✅ IMPORT ROUTERS

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
    """Setup bot commands"""
    commands = [
        BotCommand(command="start", description="🚀 Start BannerBot"),
        BotCommand(command="create", description="🎨 Create banner"),
        BotCommand(command="stats", description="📊 Stats"),
        BotCommand(command="help", description="❓ Help"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Commands registered")

async def LastPerson07_on_startup():
    """Bot startup"""
    logger.info("🔄 Starting bot...")
    await db.LastPerson07_connect()
    await db.LastPerson07_init_indexes()
    await LastPerson07_setup_commands()
    
    # ✅ REGISTER ALL ROUTERS
    dp.include_router(start.router)
    dp.include_router(banner.router)
    dp.include_router(admin.router)
    
    # ✅ REGISTER MIDDLEWARE
    dp.message.middleware(LastPerson07_AuthMiddleware())
    dp.callback_query.middleware(LastPerson07_AuthMiddleware())
    
    logger.info("✅ Bot fully initialized")

async def LastPerson07_start_bot():
    """Main bot loop"""
    try:
        await LastPerson07_on_startup()
        logger.info("🚀 Bot polling started!")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        await asyncio.sleep(5)
        await LastPerson07_start_bot()  # Restart
