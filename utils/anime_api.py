import aiohttp
import random
from loguru import logger
from PIL import Image
import io

class AnimeWallpaperAPI:
    """Real anime wallpaper API"""
    
    BASE_URLS = [
        "https://api.waifu.im/search",
        "https://api.waifu.pics/sfw/waifu",
        "https://api.waifu.pics/sfw/neko"
    ]
    
    async def get_anime_wallpaper(self) -> bytes:
        """Fetch real anime wallpaper"""
        async with aiohttp.ClientSession() as session:
            # Try waifu.im first (best quality)
            try:
                params = {
                    "included_tags": "anime,vertical",
                    "excluded_tags": "rating:explicit",
                    "height_from": "1500",
                    "width_from": "800",
                    "limit": 1
                }
                async with session.get(self.BASE_URLS[0], params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('images'):
                            img_url = data['images'][0]['url']
                            async with session.get(img_url) as img_resp:
                                if img_resp.status == 200:
                                    logger.info("✅ Anime wallpaper from waifu.im")
                                    return await img_resp.read()
            except:
                pass
            
            # Fallback to waifu.pics
            try:
                url = random.choice(self.BASE_URLS[1:])
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        img_url = data['url']
                        async with session.get(img_url) as img_resp:
                            logger.info("✅ Anime wallpaper from waifu.pics")
                            return await img_resp.read()
            except:
                pass
        
        logger.warning("❌ No anime wallpaper available")
        return None

anime_api = AnimeWallpaperAPI()
