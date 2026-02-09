# engine/pipeline.py

import asyncio
import io
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from loguru import logger

from config import config
from engine.compositor import LastPerson07_Compositor


# anime api fallback loader
try:
    from services.anime_api import anime_api
except:
    try:
        from utils.anime_api import anime_api
    except:
        anime_api = None
        logger.warning("anime_api not found. Wallpapers disabled.")


class LastPerson07_BannerEngine:
    """
    🚀 ULTRA Production Banner Engine

    Features:
    ✔ Async-safe
    ✔ Cinematic compositor
    ✔ Auto font scaling
    ✔ Glow + Stroke
    ✔ Blur panel
    ✔ Smart cleanup
    ✔ Docker safe
    ✔ High concurrency ready
    """

    def __init__(self):

        self.width = int(getattr(config, "BANNER_WIDTH", 1080))
        self.height = int(getattr(config, "BANNER_HEIGHT", 1920))
        self.quality = int(getattr(config, "BANNER_QUALITY", 90))

        self.tmp_dir = Path(
            getattr(config, "BANNER_TMP_DIR", "outputs")
        )
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        self.prefix = "banner_"
        self.keep_files = int(getattr(config, "BANNER_KEEP_FILES", 150))

        # preload fonts once (VERY IMPORTANT)
        self.font_main, self.font_small = self._load_fonts()

    # =========================================================
    # PUBLIC
    # =========================================================

    async def LastPerson07_generate(
        self,
        template_path: Optional[str] = None,
        title: str = ""
    ) -> str:

        title = (title or "").strip()[:120]

        logger.info(f"🎨 Generating banner: {title}")

        # load bg
        bg = await self._load_background(template_path)

        # 🎬 APPLY CINEMATIC COMPOSITOR
        bg = await asyncio.to_thread(
            LastPerson07_Compositor.composite,
            bg
        )

        # render text
        final_img = await asyncio.to_thread(
            self._render_text,
            bg,
            title
        )

        # export
        output_path = await asyncio.to_thread(
            self._export_image,
            final_img
        )

        asyncio.create_task(self._cleanup())

        logger.info(f"✅ Banner generated: {output_path}")

        return str(output_path)

    # =========================================================
    # BACKGROUND
    # =========================================================

    async def _load_background(self, template_path):

        # template
        if template_path:
            p = Path(template_path)
            if p.exists():
                return await asyncio.to_thread(
                    self._open_resize,
                    p
                )

        # anime fallback
        if anime_api:
            try:
                data = await anime_api.get_anime_wallpaper()
                if data:
                    return await asyncio.to_thread(
                        self._open_bytes_resize,
                        data
                    )
            except Exception as e:
                logger.warning(f"Wallpaper fetch failed: {e}")

        logger.warning("Using gradient fallback")

        return await asyncio.to_thread(
            self._gradient_bg
        )

    def _open_resize(self, path: Path):

        with Image.open(path) as im:
            im = im.convert("RGB")
            im = ImageOps.fit(
                im,
                (self.width, self.height),
                Image.Resampling.LANCZOS
            )
            return im.copy()

    def _open_bytes_resize(self, data: bytes):

        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB")
            im = ImageOps.fit(
                im,
                (self.width, self.height),
                Image.Resampling.LANCZOS
            )
            return im.copy()

    # =========================================================
    # TEXT RENDER
    # =========================================================

    def _render_text(self, bg: Image.Image, title: str):

        img = bg.convert("RGBA")

        draw = ImageDraw.Draw(img)

        font = self._auto_font(title)

        x, y = self._center(draw, title, font)

        # 🔥 BLUR PANEL (Netflix style)
        panel_box = (
            int(self.width * 0.05),
            y - 40,
            int(self.width * 0.95),
            y + 200
        )

        img = LastPerson07_Compositor.blur_panel(
            img,
            panel_box
        )

        # glow layer
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)

        glow_draw.text(
            (x, y),
            title,
            font=font,
            fill=(120, 170, 255, 180)
        )

        glow = glow.filter(
            ImageFilter.GaussianBlur(12)
        )

        img = Image.alpha_composite(img, glow)

        # stroke
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx or dy:
                    draw.text(
                        (x + dx, y + dy),
                        title,
                        font=font,
                        fill=(0, 0, 0)
                    )

        # main text
        draw.text(
            (x, y),
            title,
            font=font,
            fill=(255, 255, 255)
        )

        # watermark
        draw.text(
            (30, 30),
            getattr(config, "WATERMARK_TEXT", "@LastPerson07"),
            font=self.font_small,
            fill=(210, 210, 210)
        )

        return img.convert("RGB")

    # =========================================================
    # FONTS
    # =========================================================

    def _load_fonts(self):

        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "assets/fonts/Inter-Bold.ttf",
        ]

        for fp in font_paths:
            if Path(fp).exists():
                return (
                    ImageFont.truetype(fp, self.width // 14),
                    ImageFont.truetype(fp, self.width // 32)
                )

        logger.warning("No font found — using default")

        return (
            ImageFont.load_default(),
            ImageFont.load_default()
        )

    def _auto_font(self, text):

        size = self.width // 14

        while size > 30:
            try:
                font = ImageFont.truetype(
                    self.font_main.path,
                    size
                )
            except:
                return self.font_main

            dummy = Image.new("RGB", (10, 10))
            d = ImageDraw.Draw(dummy)

            bbox = d.textbbox((0, 0), text, font=font)

            if bbox[2] < self.width * 0.9:
                return font

            size -= 4

        return self.font_main

    def _center(self, draw, text, font):

        bbox = draw.textbbox((0, 0), text, font=font)

        w = bbox[2]
        h = bbox[3]

        return (
            (self.width - w) // 2,
            (self.height - h) // 2 - 120
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def _export_image(self, image):

        fd, path = tempfile.mkstemp(
            prefix=self.prefix,
            suffix=".jpg",
            dir=self.tmp_dir
        )

        os.close(fd)

        image.save(
            path,
            "JPEG",
            quality=self.quality,
            optimize=True,
            progressive=True
        )

        return Path(path)

    # =========================================================
    # CLEANUP
    # =========================================================

    async def _cleanup(self):

        try:
            files = list(
                self.tmp_dir.glob(f"{self.prefix}*.jpg")
            )

            if len(files) <= self.keep_files:
                return

            files.sort(
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for f in files[self.keep_files:]:
                try:
                    f.unlink()
                except:
                    pass

        except Exception as e:
            logger.debug(f"cleanup failed: {e}")

    # =========================================================
    # GRADIENT
    # =========================================================

    def _gradient_bg(self):

        img = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(img)

        for y in range(self.height):

            r = int(18 + (y / self.height) * 45)
            g = int(12 + (y / self.height) * 28)
            b = int(38 + (y / self.height) * 90)

            draw.line(
                [(0, y), (self.width, y)],
                fill=(r, g, b)
            )

        return img


banner_engine = LastPerson07_BannerEngine()
