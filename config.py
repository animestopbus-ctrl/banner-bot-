import os
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger  # ✅ ADDED MISSING IMPORT

load_dotenv()

class Config:
    """Production configuration"""
    
    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    
    # Database
    MONGO_URI = os.getenv("MONGO_URI", "").strip()
    
    # Admin
    ADMIN_IDS = [
        int(x.strip())
        for x in os.getenv("ADMIN_IDS", "").split(",")
        if x.strip().isdigit()
    ]
    
    # Server
    PORT = int(os.getenv("PORT", 10000))
    HOST = "0.0.0.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent
    TEMPLATES_DIR = BASE_DIR / "templates"
    ASSETS_DIR = BASE_DIR / "assets"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories
    LOGS_DIR.mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    
    # Image settings
    BANNER_WIDTH = 1080
    BANNER_HEIGHT = 1920
    BANNER_QUALITY = 90
    MAX_TITLE_LENGTH = 60
    
    def validate(self):
        """Validate configuration"""
        if not self.BOT_TOKEN or len(self.BOT_TOKEN) < 10:
            raise ValueError("❌ Invalid BOT_TOKEN!")
        if not self.MONGO_URI:
            raise ValueError("❌ MONGO_URI not set!")
        logger.info("✅ Configuration validated")  # ✅ NOW WORKS
        return True

config = Config()
