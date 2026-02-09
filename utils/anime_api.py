import aiohttp
import io
from loguru import logger
from PIL import Image

async def LastPerson07_get_wallpaper() -> bytes:
    """Fetch anime wallpaper from public APIs"""
    try:
        urls = [
            "https://picsum.photos/1080/1920.jpg?random=1",
            "https://picsum.photos/seed/anime/1080/1920",
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            logger.info(f"✅ Wallpaper fetched from {url}")
                            return data
                except Exception as e:
                    logger.debug(f"URL failed {url}: {e}")
                    continue
        
        logger.warning("No wallpaper sources available")
        return None
        
    except Exception as e:
        logger.error(f"Wallpaper fetch error: {e}")
        return None
