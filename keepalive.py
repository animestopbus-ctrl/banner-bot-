import os
import sys
import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import config
from bot import LastPerson07_start_bot  # ✅ FIXED IMPORT

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting LastPerson07x-BannerBot v3.1")
    try:
        config.validate()
        # ✅ PROPER ASYNC BOT START
        asyncio.create_task(LastPerson07_start_bot())
        logger.info("✅ Bot task started")
        yield
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        yield

app = FastAPI(title="BannerBot v3.1", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "🟢 BannerBot v3.1 RUNNING ✅"}

@app.get("/health")
async def health():
    try:
        from database.mongo import db
        await db.LastPerson07_ping()
        return {"status": "healthy", "bot": "running"}
    except:
        return {"status": "unhealthy"}, 503

if __name__ == "__main__":
    import uvicorn
    port = config.PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
