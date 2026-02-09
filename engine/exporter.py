from PIL import Image
from loguru import logger
from pathlib import Path
import tempfile
import os
import asyncio
from typing import Optional


class LastPerson07_Exporter:
    """
    Professional Image Exporter

    ✔ Progressive JPEG
    ✔ Optimized compression
    ✔ Thread-safe saving
    ✔ Automatic cleanup
    ✔ Configurable directory
    ✔ Predictable filenames
    ✔ Non-blocking support
    """

    DEFAULT_PREFIX = "banner_"
    KEEP_FILES = 200

    # ---------------- EXPORT ---------------- #

    @staticmethod
    async def export_async(
        image: Image.Image,
        output_dir: Optional[str] = None,
        quality: int = 88
    ) -> str:
        """
        Async-safe export.
        Runs Pillow inside threadpool.
        """

        return await asyncio.to_thread(
            LastPerson07_Exporter._export_sync,
            image,
            output_dir,
            quality
        )

    # ---------------- SYNC CORE ---------------- #

    @staticmethod
    def _export_sync(
        image: Image.Image,
        output_dir: Optional[str],
        quality: int
    ) -> str:

        try:
            # Choose directory
            if output_dir:
                out_dir = Path(output_dir)
            else:
                out_dir = Path("outputs")

            out_dir.mkdir(parents=True, exist_ok=True)

            # Create temp file safely
            fd, path = tempfile.mkstemp(
                prefix=LastPerson07_Exporter.DEFAULT_PREFIX,
                suffix=".jpg",
                dir=str(out_dir)
            )
            os.close(fd)

            output_path = Path(path)

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 🔥 SAVE WITH MAX OPTIMIZATION
            image.save(
                output_path,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling=0  # highest quality chroma
            )

            logger.info(f"✅ Exported banner -> {output_path}")

            # Cleanup old files
            LastPerson07_Exporter._cleanup(out_dir)

            return str(output_path)

        except Exception as e:
            logger.exception(f"Export failed: {e}")
            raise

    # ---------------- CLEANUP ---------------- #

    @staticmethod
    def _cleanup(directory: Path):
        """
        Keep only latest N banners.
        Extremely important for Docker servers.
        """

        try:
            files = list(directory.glob(f"{LastPerson07_Exporter.DEFAULT_PREFIX}*.jpg"))

            if len(files) <= LastPerson07_Exporter.KEEP_FILES:
                return

            # sort by modification time
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            old_files = files[LastPerson07_Exporter.KEEP_FILES:]

            for file in old_files:
                try:
                    file.unlink()
                except Exception:
                    pass

            logger.info(f"🧹 Cleaned {len(old_files)} old banners")

        except Exception as e:
            logger.debug(f"Cleanup skipped: {e}")
