import aiohttp
import random
from loguru import logger


class AnimeWallpaperAPI:
    """
    Production-level Anime Wallpaper Fetcher
    Fast + resilient + proper fallbacks
    """

    WAIFU_IM = "https://api.waifu.im/search"
    WAIFU_PICS = [
        "https://api.waifu.pics/sfw/waifu",
        "https://api.waifu.pics/sfw/neko"
    ]

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None

    async def start(self):
        """Create ONE session for the entire bot lifecycle"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session:
            await self.session.close()

    async def _download_image(self, url: str) -> bytes | None:
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            logger.warning(f"Image download failed: {e}")
        return None

    async def get_anime_wallpaper(self) -> bytes | None:
        """
        Returns RAW image bytes
        """

        if not self.session:
            await self.start()

        # 🔥 TRY WAIFU.IM (BEST QUALITY)
        try:
            params = {
                "included_tags": "waifu",
                "height_from": "1400",
                "width_from": "800",
                "limit": 1
            }

            async with self.session.get(self.WAIFU_IM, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if data.get("images"):
                        url = data["images"][0]["url"]
                        img = await self._download_image(url)

                        if img:
                            logger.info("✅ Wallpaper: waifu.im")
                            return img

        except Exception as e:
            logger.warning(f"waifu.im failed: {e}")

        # 🔥 FALLBACK — WAIFU.PICS
        try:
            url = random.choice(self.WAIFU_PICS)

            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img = await self._download_image(data["url"])

                    if img:
                        logger.info("✅ Wallpaper: waifu.pics")
                        return img

        except Exception as e:
            logger.warning(f"waifu.pics failed: {e}")

        logger.error("❌ ALL wallpaper APIs failed")
        return None


# SINGLETON (important)
anime_api = AnimeWallpaperAPI()
