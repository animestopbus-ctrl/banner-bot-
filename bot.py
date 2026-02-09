# bot.py

import asyncio
import sys
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger

from config import config
from database.mongo import db
from middlewares.auth import LastPerson07_AuthMiddleware
from handlers import start, banner, admin


# =====================================================
# LOGGING
# =====================================================

logger.remove()

logger.add(
    str(config.LOGS_DIR / "bot.log"),
    rotation="5 MB",
    retention="10 days",
    compression="zip",
    level="INFO"
)

logger.add(sys.stdout, level="INFO")


# =====================================================
# GLOBALS
# =====================================================

bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None
_registered = False


# =====================================================
# COMMANDS
# =====================================================

async def setup_commands(bot_obj: Bot):

    commands = [
        BotCommand(command="start", description="🚀 Start BannerBot"),
        BotCommand(command="create", description="🎨 Create banner"),
        BotCommand(command="stats", description="📊 Statistics"),
        BotCommand(command="help", description="❓ Help"),
    ]

    await bot_obj.set_my_commands(commands)

    logger.info("✅ Bot commands registered")


# =====================================================
# ROUTERS + MIDDLEWARE
# =====================================================

async def register_handlers(dispatcher: Dispatcher):

    global _registered

    if _registered:
        return

    dispatcher.include_router(start.router)
    dispatcher.include_router(banner.router)
    dispatcher.include_router(admin.router)

    auth = LastPerson07_AuthMiddleware()

    dispatcher.message.middleware(auth)
    dispatcher.callback_query.middleware(auth)

    _registered = True

    logger.info("✅ Routers & middlewares registered")


# =====================================================
# STARTUP
# =====================================================

async def startup():

    global bot, dp

    config.validate()

    # Mongo connection
    await db.connect()

    # Create bot once
    if bot is None:

        bot_props = DefaultBotProperties(
            parse_mode="HTML"
        )

        bot = Bot(
            token=config.BOT_TOKEN,
            default=bot_props
        )

        logger.info("✅ Bot instance created")

    # Dispatcher once
    if dp is None:

        dp = Dispatcher(
            storage=MemoryStorage()
        )

        logger.info("✅ Dispatcher created")

    await register_handlers(dp)

    await setup_commands(bot)

    logger.info("✅ Bot startup complete")


# =====================================================
# SHUTDOWN
# =====================================================

async def shutdown():

    global bot, dp

    logger.info("🛑 Shutting down bot...")

    try:
        if dp:
            await dp.shutdown()
            logger.info("✅ Dispatcher stopped")

    except Exception as e:
        logger.exception(f"Dispatcher shutdown error: {e}")

    try:
        if bot:
            await bot.session.close()
            logger.info("✅ Bot session closed")

    except Exception as e:
        logger.exception(f"Bot shutdown error: {e}")

    await db.close()


# =====================================================
# MAIN LOOP
# =====================================================

async def LastPerson07_start_bot():

    backoff = 2
    max_backoff = 60

    while True:

        try:

            await startup()

            if not bot or not dp:
                raise RuntimeError("Bot failed to initialize")

            logger.info("🚀 Starting polling...")

            await dp.start_polling(
                bot,
                skip_updates=True
            )

            # clean exit
            break

        except asyncio.CancelledError:

            logger.info("Bot task cancelled")

            await shutdown()
            break

        except Exception as e:

            logger.exception(f"🔥 Bot crashed: {e}")

            await shutdown()

            logger.info(f"Restarting in {backoff}s...")

            await asyncio.sleep(backoff)

            backoff = min(max_backoff, backoff * 2)
