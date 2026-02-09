# services/banner_service.py

from pathlib import Path
from typing import Optional
from loguru import logger

from engine.pipeline import banner_engine


class LastPerson07_BannerService:
    """
    🚀 Production Banner Service

    Lightweight wrapper around banner_engine.

    ✔ No fake async
    ✔ No disk duplication
    ✔ Singleton engine
    ✔ Docker safe
    ✔ Fast
    ✔ Scalable
    """

    def __init__(self):
        self.engine = banner_engine
        self.templates_dir = Path("templates")

    # =====================================================
    # PUBLIC
    # =====================================================

    async def LastPerson07_create_banner(
        self,
        title: str,
        template_id: str = "1"
    ) -> str:
        """
        Generate banner and return file path.
        """

        title = (title or "").strip()

        if not title:
            raise ValueError("Title cannot be empty")

        template_path = self._resolve_template(template_id)

        try:
            output_path = await self.engine.LastPerson07_generate(
                template_path=template_path,
                title=title
            )

            logger.info(f"✅ Banner created: {output_path}")

            return output_path

        except Exception as e:
            logger.exception(f"Banner generation failed: {e}")
            raise

    # =====================================================
    # TEMPLATE RESOLUTION
    # =====================================================

    def _resolve_template(self, template_id: str) -> Optional[str]:
        """
        Resolve template safely.
        Falls back to wallpaper if missing.
        """

        template_map = {
            "1": self.templates_dir / "template1.jpg",
            "2": self.templates_dir / "template2.jpg",
            "3": self.templates_dir / "template3.jpg",
            "4": self.templates_dir / "template4.jpg",
        }

        template = template_map.get(template_id)

        if template and template.exists():
            return str(template)

        logger.warning(f"Template missing → fallback to anime wallpaper ({template_id})")

        return None


# ⭐ GLOBAL SINGLETON (IMPORTANT)
banner_service = LastPerson07_BannerService()
