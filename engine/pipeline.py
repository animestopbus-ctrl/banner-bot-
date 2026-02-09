\# engine/pipeline.py
import asyncio
import io
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from loguru import logger

from config import config

# Try importing anime_api from services first, then utils (compatibility)
try:
    from services.anime_api import anime_api
except Exception:
    try:
        from utils.anime_api import anime_api
    except Exception:
        anime_api = None
        logger.warning("anime_api not found in services or utils. Wallpaper fallback may be limited.")


class LastPerson07_BannerEngine:
    """🎨 Production-ready banner generation engine."""

    def __init__(self):
        # Use config values with fallbacks
        self.width = int(getattr(config, "BANNER_WIDTH", 1080))
        self.height = int(getattr(config, "BANNER_HEIGHT", 1920))
        self.quality = int(getattr(config, "BANNER_QUALITY", 88))
        # Where to store temporary banners (ensure writable)
        tmp_dir = getattr(config, "BANNER_TMP_DIR", None)
        if tmp_dir:
            self.tmp_dir = Path(tmp_dir)
        else:
            # prefer local outputs folder inside project, fallback to /tmp
            self.tmp_dir = Path("outputs")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Prefix used for temp files so cleanup can identify them
        self._file_prefix = "banner_"
        # how many temp files to keep
        self._keep_files = int(getattr(config, "BANNER_KEEP_FILES", 200))

    # ---------------- public API ---------------- #

    async def LastPerson07_generate(
        self,
        template_path: Optional[str] = None,
        title: str = ""
    ) -> str:
        """
        Generate an HD banner and return the path to the saved image (JPEG).

        This method is async but most heavy work is run in a threadpool to avoid blocking.
        """
        title = (title or "").strip()
        if len(title) > getattr(config, "MAX_TITLE_LENGTH", 120):
            title = title[: getattr(config, "MAX_TITLE_LENGTH", 120)]

        logger.info(f"🎨 Generating banner: '{title}' (template={template_path})")

        # 1. Load / prepare background (may perform network IO -> run in thread)
        bg = await self._load_background(template_path)

        # 2. Apply overlay for readability
        bg = await asyncio.to_thread(self._apply_overlay, bg)

        # 3. Draw text (run in thread)
        try:
            output_image = await asyncio.to_thread(self._render_text_and_watermark, bg, title)
        except Exception as e:
            logger.exception(f"Failed while rendering text: {e}")
            raise

        # 4. Export to file (non-blocking via thread)
        out_path = await asyncio.to_thread(self._export_image, output_image)

        logger.info(f"✅ Banner generated: {out_path}")
        # schedule cleanup (fire-and-forget)
        asyncio.create_task(self._cleanup_temp_files())

        return str(out_path)

    # ---------------- background loading ---------------- #

    async def _load_background(self, template_path: Optional[str]) -> Image.Image:
        """
        Attempt to load template -> anime wallpaper -> gradient fallback.
        Network and file operations executed in threads.
        """
        # 1) Template
        if template_path:
            try:
                p = Path(template_path)
                if p.exists():
                    return await asyncio.to_thread(self._open_and_resize, p)
                else:
                    logger.warning(f"Template not found: {template_path}")
            except Exception as e:
                logger.warning(f"Failed to load template {template_path}: {e}")

        # 2) Anime API fallback (if available)
        if anime_api is not None:
            try:
                data = await anime_api.get_anime_wallpaper()
                if data:
                    return await asyncio.to_thread(self._open_bytes_and_resize, data)
                else:
                    logger.warning("anime_api returned no data.")
            except Exception as e:
                logger.warning(f"anime_api fetch failed: {e}")

        # 3) Gradient fallback
        logger.warning("Using gradient fallback background.")
        return await asyncio.to_thread(self._create_gradient_bg)

    def _open_and_resize(self, path: Path) -> Image.Image:
        """Blocking: open & resize image from disk"""
        with Image.open(path) as im:
            im = im.convert("RGB")
            im = ImageOps.fit(im, (self.width, self.height), Image.Resampling.LANCZOS)
            return im.copy()

    def _open_bytes_and_resize(self, data: bytes) -> Image.Image:
        """Blocking: open & resize image from bytes"""
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB")
            im = ImageOps.fit(im, (self.width, self.height), Image.Resampling.LANCZOS)
            return im.copy()

    # ---------------- visual helpers ---------------- #

    def _apply_overlay(self, bg: Image.Image) -> Image.Image:
        """Apply a semi-transparent dark overlay for better text contrast."""
        if bg.mode != "RGBA":
            base = bg.convert("RGBA")
        else:
            base = bg.copy()

        overlay_alpha = int(getattr(config, "OVERLAY_ALPHA", 140))
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, overlay_alpha))
        composed = Image.alpha_composite(base, overlay).convert("RGB")
        return composed

    def _load_fonts(self) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
        """
        Load fonts with dynamic sizes based on banner width.
        Falls back to PIL default if no truetype font found.
        """
        # dynamic sizes
        main_size = max(36, self.width // 18)  # for 1080 -> 60
        small_size = max(18, self.width // 30)

        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            str(Path("assets/fonts/Inter-Bold.ttf")),
            str(Path("assets/fonts/Roboto-Bold.ttf")),
        ]

        font_main = None
        font_small = None

        for fp in font_candidates:
            try:
                p = Path(fp)
                if p.exists():
                    font_main = ImageFont.truetype(fp, main_size)
                    font_small = ImageFont.truetype(fp, small_size)
                    break
            except Exception:
                continue

        if font_main is None:
            logger.warning("No TTF font found; falling back to default bitmap font.")
            font_main = ImageFont.load_default()
            font_small = ImageFont.load_default()

        return font_main, font_small

    def _calculate_text_position(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
        """Calculate a sensible centered position for the title (with upward offset)."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (self.width - text_w) // 2
        y = (self.height - text_h) // 2 - (self.height // 8)  # lift a bit for visual balance
        return x, y

    def _render_text_and_watermark(self, bg: Image.Image, title: str) -> Image.Image:
        """
        Blocking: draw glow text, outline, and watermark onto an image and return the final image.
        Uses a separate glow layer and Gaussian blur for smoothness.
        """
        if bg.mode != "RGBA":
            base = bg.convert("RGBA")
        else:
            base = bg.copy()

        draw = ImageDraw.Draw(base)
        font_main, font_small = self._load_fonts()

        # Prepare glow layer
        glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        # Text params
        text = title or ""
        # reduce font size if text too wide
        # gradually shrink font_main if exceeds width * 0.9
        fm = font_main
        if hasattr(fm, "getsize"):
            w_limit = int(self.width * 0.9)
            bbox = glow_draw.textbbox((0, 0), text, font=fm)
            while bbox[2] - bbox[0] > w_limit and getattr(fm, "size", None):
                # rebuild font with smaller size
                new_size = max(18, int(getattr(fm, "size", 0) * 0.9))
                try:
                    fm = ImageFont.truetype(fm.path, new_size)  # type: ignore[attr-defined]
                except Exception:
                    break
                bbox = glow_draw.textbbox((0, 0), text, font=fm)

        x, y = self._calculate_text_position(glow_draw, text, fm)

        # Draw glow (white text on glow layer, then blur and tint)
        glow_color = (120, 160, 255, 180)  # light blue-ish
        glow_draw.text((x, y), text, font=fm, fill=glow_color)

        # Apply blur to create outer glow
        blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=max(8, self.width // 150)))

        # Optionally tint the glow by compositing a semi-transparent colored layer
        base = Image.alpha_composite(base, blurred)

        # Draw strong black stroke (outline) by drawing text multiple times offset
        stroke_color = (0, 0, 0, 255)
        stroke_range = max(2, self.width // 540)  # ~2-3 for 1080 width
        for dx in range(-stroke_range, stroke_range + 1):
            for dy in range(-stroke_range, stroke_range + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=fm, fill=stroke_color)

        # Draw main text (white)
        draw.text((x, y), text, font=fm, fill=(255, 255, 255, 255))

        # Draw watermark top-left using small font
        watermark = getattr(config, "WATERMARK_TEXT", "@LastPerson07")
        ws = watermark
        w_font = font_small
        try:
            draw.text((20, 20), ws, font=w_font, fill=(200, 200, 200, 180))
        except Exception:
            pass

        # Final enhancement (slight contrast/brightness tweak)
        try:
            final = base.convert("RGB")
            enhancer = ImageOps.autocontrast(final, cutoff=0)
            return enhancer
        except Exception:
            return base.convert("RGB")

    # ---------------- export & cleanup ---------------- #

    def _export_image(self, image: Image.Image) -> Path:
        """
        Blocking: write image to disk and return path.
        We use a predictable prefix so cleanup can find files easily.
        """
        # ensure directory exists
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        fd, path = tempfile.mkstemp(prefix=self._file_prefix, suffix=".jpg", dir=str(self.tmp_dir))
        os.close(fd)  # mkstemp gives open fd — close it because Pillow will write the file
        out_path = Path(path)

        # Save using Pillow (blocking)
        image.save(str(out_path), "JPEG", quality=self.quality, optimize=True, progressive=True)

        return out_path

    async def _cleanup_temp_files(self) -> None:
        """Asynchronously remove old banner files, keeping the newest N files."""
        try:
            files = list(self.tmp_dir.glob(f"{self._file_prefix}*.jpg"))
            if len(files) <= self._keep_files:
                return
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            to_remove = files[self._keep_files :]
            for p in to_remove:
                try:
                    p.unlink()
                except Exception:
                    logger.debug(f"Failed to remove temp banner {p}")
        except Exception as e:
            logger.debug(f"Cleanup failed: {e}")


# single, reusable instance
banner_engine = LastPerson07_BannerEngine()
