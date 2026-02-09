import os
import sys
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import bot and config
from bot import LastPerson07_start_bot_safe
from config import config

startup_done = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown"""
    global startup_done
    
    logger.info("=" * 60)
    logger.info("🚀 Starting LastPerson07x-BannerBot v3.0")
    logger.info("=" * 60)
    
    try:
        # Validate config
        config.validate()
        logger.info("✅ Config validated")
        
        # Start bot
        bot_task = asyncio.create_task(LastPerson07_start_bot_safe())
        startup_done = True
        logger.info("✅ Bot started successfully")
        
        yield
        
        # Shutdown
        logger.info("🛑 Shutting down...")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}", exc_info=True)
        startup_done = False
        yield
        sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="LastPerson07x-BannerBot",
    version="3.0",
    description="Professional Telegram Banner Generator",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root health check"""
    status = "🟢 RUNNING" if startup_done else "🟡 STARTING"
    return {
        "status": status,
        "service": "LastPerson07x-BannerBot v3.0",
        "message": "Professional Telegram Banner Generator"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        from database.mongo import db
        ping_result = await db.LastPerson07_ping()
        return {
            "status": "healthy",
            "database": "✅" if ping_result else "❌",
            "bot": "✅" if startup_done else "❌"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}, 503

@app.get("/metrics")
async def metrics():
    """Bot metrics"""
    try:
        from database.mongo import db
        stats = await db.LastPerson07_get_stats()
        return {
            "total_users": stats.get('total_users', 0),
            "total_banners": stats.get('total_banners', 0),
            "active_24h": stats.get('active_24h', 0),
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}, 500

def run_server():
    """Run FastAPI server"""
    import uvicorn
    
    port = config.PORT
    host = config.HOST
    
    logger.info(f"📡 Starting server on {host}:{port}")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False
        )
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_server()
