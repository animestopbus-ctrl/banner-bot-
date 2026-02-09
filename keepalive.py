import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from loguru import logger

from config import config
from bot import LastPerson07_start_bot
from database.mongo import db
from services.anime_api import anime_api


# ---------------- LIFECYCLE ---------------- #

bot_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Production lifecycle manager
    Handles startup + shutdown safely
    """

    global bot_task

    logger.info("🚀 Starting LastPerson07x-BannerBot v3.1")

    try:
        # ✅ Validate config early
        config.validate()

        # ✅ Connect Mongo BEFORE bot starts
        await db.connect()

        # ✅ Start Anime API session
        await anime_api.start()

        # ✅ Start bot polling in background
        bot_task = asyncio.create_task(
            LastPerson07_start_bot(),
            name="telegram-bot"
        )

        logger.info("✅ Bot started successfully")

        yield

    except Exception as e:
        logger.exception(f"❌ Startup failure: {e}")
        raise

    # ---------------- SHUTDOWN ---------------- #

    logger.warning("🛑 Shutting down BannerBot...")

    if bot_task:
        bot_task.cancel()

        try:
            await bot_task
        except asyncio.CancelledError:
            logger.info("✅ Bot task cancelled")

    # Close anime session
    await anime_api.close()

    logger.info("✅ Shutdown complete")


# ---------------- FASTAPI ---------------- #

app = FastAPI(
    title="LastPerson07x BannerBot",
    version="3.1",
    lifespan=lifespan
)


# ---------------- ROUTES ---------------- #

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "BannerBot",
        "version": "3.1"
    }


@app.get("/health")
async def health():
    """
    REAL health check.
    Not fake 'ok'.
    """

    try:
        await db.client.admin.command("ping")

        if bot_task and not bot_task.done():
            return {
                "status": "healthy",
                "bot": "running",
                "database": "connected"
            }

        raise Exception("Bot task not running")

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )


# ---------------- LOCAL RUN ---------------- #

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",   # 🔥 important for reload & workers
        host="0.0.0.0",
        port=config.PORT,
        log_level="info"
    )
