# services/banner_service.py
import asyncio
import inspect
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Union

from loguru import logger
from PIL import Image
from engine.pipeline import LastPerson07_BannerEngine

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class LastPerson07_BannerService:
    """Banner generation service (production-ready).

    Usage:
        svc = LastPerson07_BannerService()
        out_path = await svc.LastPerson07_create_banner("My Title", template_id="1")
    """

    def __init__(self):
        # engine may be heavy -> instantiate once
        self.engine = LastPerson07_BannerEngine()
        self.templates_dir = Path("templates")

    async def _maybe_await(self, result):
        """If result is awaitable, await it; otherwise return as-is."""
        if inspect.isawaitable(result):
            return await result
        return result

    async def _run_sync_in_thread(self, func, *args, **kwargs):
        """Run potentially blocking sync function in a thread pool."""
        return await asyncio.to_thread(lambda: func(*args, **kwargs))

    async def _call_engine_generate(
        self, template_path: Optional[str], title: str
    ) -> Union[bytes, str]:
        """
        Call engine.LastPerson07_generate in a safe way:
        - If engine.LastPerson07_generate is async -> await it
        - If it's sync -> run in thread and return result
        """
        gen = getattr(self.engine, "LastPerson07_generate", None)
        if gen is None:
            raise RuntimeError("Banner engine missing LastPerson07_generate method")

        try:
            # If the engine method is a coroutine function, call it and await.
            if inspect.iscoroutinefunction(gen):
                result = await gen(template_path=template_path, title=title)
                return result

            # If engine method is regular function, run in thread
            result = await self._run_sync_in_thread(gen, template_path, title)
            return result

        except Exception:
            logger.exception("Engine generate failed")
            raise

    async def LastPerson07_create_banner(
        self,
        title: str,
        template_id: str = "1"
    ) -> str:
        """
        Create a banner with given title and template.

        Args:
            title: Banner title text (will be used by the engine)
            template_id: Template ID (e.g. "1", "2", ...)

        Returns:
            Path (string) to generated banner image on disk.
        """
        # Basic validation & sanitization
        title = (title or "").strip()
        if not title:
            raise ValueError("title must be a non-empty string")

        # template mapping (falls back to None if missing)
        template_map = {
            "1": self.templates_dir / "template1.jpg",
            "2": self.templates_dir / "template2.jpg",
            "3": self.templates_dir / "template3.jpg",
            "4": self.templates_dir / "template4.jpg",
        }
        tpl_path_obj = template_map.get(template_id, template_map["1"])
        if not tpl_path_obj.exists():
            logger.warning(f"Template not found: {tpl_path_obj}. Engine default will be used.")
            tpl_path: Optional[str] = None
        else:
            tpl_path = str(tpl_path_obj)

        # Call engine safely (sync or async)
        result = await self._call_engine_generate(template_path=tpl_path, title=title)

        # The engine may return either: bytes (raw image) or a path string.
        # Normalize both into a file on disk and return the path.
        try:
            if isinstance(result, (bytes, bytearray)):
                # Write bytes to a new file in outputs/
                filename = f"banner_{uuid.uuid4().hex}.jpg"
                out_path = OUTPUT_DIR / filename

                # validate and save image via PIL to ensure correct format
                try:
                    img = Image.open(tempfile.SpooledTemporaryFile())
                except Exception:
                    # We'll create image from bytes directly
                    pass

                # Use Pillow to open bytes and re-save as optimized JPG
                from io import BytesIO

                bio = BytesIO(result)
                try:
                    with Image.open(bio) as img:
                        rgb = img.convert("RGB")
                        rgb.save(out_path, format="JPEG", quality=92, optimize=True)
                except Exception:
                    # If Pillow fails, write raw bytes as a fallback
                    out_path.write_bytes(result)

                logger.info(f"✅ Banner written to {out_path}")
                return str(out_path)

            elif isinstance(result, str):
                # Engine returned a path. Validate it and copy/normalize into outputs/
                src = Path(result)
                if not src.exists():
                    logger.warning(f"Engine returned path but file not found: {src}")
                    raise FileNotFoundError(f"Engine returned missing file: {src}")

                # Ensure consistent output filename
                dest = OUTPUT_DIR / f"banner_{uuid.uuid4().hex}{src.suffix or '.jpg'}"
                # Copy the file asynchronously using thread to avoid blocking
                await self._run_sync_in_thread(lambda: dest.write_bytes(src.read_bytes()))
                logger.info(f"✅ Banner copied to {dest}")
                return str(dest)

            else:
                logger.error(f"Unexpected engine return type: {type(result)}")
                raise TypeError("Engine returned unsupported type (expected bytes or path string)")

        except Exception:
            logger.exception("Failed to persist banner output")
            raise
