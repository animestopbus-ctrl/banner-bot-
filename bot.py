# bot.py
import asyncio
import sys
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger

from config import config
from database.mongo import db
from middlewares.auth import LastPerson07_AuthMiddleware
from handlers import start, banner, admin  # routers

# Setup loguru
logger.remove()
logger.add(
    str(config.LOGS_DIR / "bot.log"),
    rotation="1 MB",
    retention="7 days",
    level="INFO"
)
logger.add(sys.stdout, level="INFO")

# Globals that will be created at startup
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

# internal flag to ensure routers/middlewares registered once
_registered = False


async def LastPerson07_setup_commands(bot_obj: Bot):
    """Idempotent: set bot commands"""
    commands = [
        BotCommand(command="start", description="🚀 Start BannerBot"),
        BotCommand(command="create", description="🎨 Create banner"),
        BotCommand(command="stats", description="📊 Stats"),
        BotCommand(command="help", description="❓ Help"),
    ]
    try:
        await bot_obj.set_my_commands(commands)
        logger.info("✅ Commands registered")
    except Exception as e:
        logger.exception(f"Failed to set commands: {e}")


async def _register_handlers_and_middlewares(dispatcher: Dispatcher):
    """Register routers & middlewares only once"""
    global _registered
    if _registered:
        return

    # register routers
    dispatcher.include_router(start.router)
    dispatcher.include_router(banner.router)
    dispatcher.include_router(admin.router)

    # register middlewares (message & callback)
    auth_mw = LastPerson07_AuthMiddleware()
    dispatcher.message.middleware(auth_mw)
    dispatcher.callback_query.middleware(auth_mw)

    _registered = True
    logger.info("✅ Routers and middlewares registered")


async def LastPerson07_on_startup():
    """Startup routine: connect DB, create bot/dispatcher, register handlers."""
    global bot, dp

    # validate config early
    config.validate()

    # Ensure DB connected and indexes ready
    await db.connect()             # uses new db.connect()
    await db.init_indexes()        # idempotent

    # Create Bot & Dispatcher instances if not created
    if bot is None:
        bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
        logger.info("✅ Bot instance created")

    if dp is None:
        dp = Dispatcher(storage=MemoryStorage())
        logger.info("✅ Dispatcher instance created")

    # Register handlers and middlewares once
    await _register_handlers_and_middlewares(dp)

    # Register commands (idempotent)
    await LastPerson07_setup_commands(bot)

    logger.info("✅ Bot fully initialized")


async def LastPerson07_shutdown():
    """Gracefully shutdown bot and dispatcher"""
    global bot, dp

    logger.info("🛑 Shutting down bot...")

    try:
        if dp is not None:
            # aiogram v3: dispatcher.shutdown handles cleanup
            await dp.shutdown()
            logger.info("✅ Dispatcher shutdown")
    except Exception as e:
        logger.exception(f"Error shutting down dispatcher: {e}")

    try:
        if bot is not None:
            await bot.session.close()  # close underlying aiohttp session
            # also call close() for completeness
            try:
                await bot.close()
            except Exception:
                pass
            logger.info("✅ Bot closed")
    except Exception as e:
        logger.exception(f"Error closing bot: {e}")


async def LastPerson07_start_bot():
    """
    Main bot loop.
    Uses an automatic restart loop with backoff on unexpected crashes,
    but handles asyncio.CancelledError (task cancellation) gracefully.
    """
    global bot, dp

    backoff = 1
    max_backoff = 30

    while True:
        try:
            await LastPerson07_on_startup()

            if bot is None or dp is None:
                raise RuntimeError("Bot or Dispatcher not initialized")

            logger.info("🚀 Starting polling (skip_updates=True)")
            # start_polling will block until cancelled or finished
            await dp.start_polling(bot, skip_updates=True)

            # If start_polling returns normally, break the loop (clean exit)
            logger.info("Polling stopped normally")
            break

        except asyncio.CancelledError:
            # Task was cancelled by outer lifecycle manager -> shutdown cleanly
            logger.info("Bot task cancelled; performing clean shutdown")
            await LastPerson07_shutdown()
            break

        except Exception as e:
            # Unexpected error -> log, backoff, then restart
            logger.exception(f"Bot crashed with error: {e}")
            logger.info(f"Restarting in {backoff} seconds...")
            await LastPerson07_shutdown()
            await asyncio.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)  # exponential backoff
            continue
