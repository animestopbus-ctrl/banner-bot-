import os
from pathlib import Path
from engine.pipeline import LastPerson07_BannerEngine
from loguru import logger
import tempfile

class LastPerson07_BannerService:
    """Banner generation service"""
    
    def __init__(self):
        self.engine = LastPerson07_BannerEngine()
        self.templates_dir = Path("templates")
    
    async def LastPerson07_create_banner(
        self,
        title: str,
        template_id: str = "1"
    ) -> str:
        """
        Create a banner with given title and template
        
        Args:
            title: Banner title text
            template_id: Template ID (1-4)
        
        Returns:
            Path to generated banner image
        """
        try:
            # Map template ID to file
            template_map = {
                "1": self.templates_dir / "template1.jpg",
                "2": self.templates_dir / "template2.jpg",
                "3": self.templates_dir / "template3.jpg",
                "4": self.templates_dir / "template4.jpg",
            }
            
            template_path = template_map.get(template_id, template_map["1"])
            
            # Check if template exists
            if not template_path.exists():
                logger.warning(f"Template not found: {template_path}")
                template_path = None
            
            # Generate banner
            output_path = await self.engine.LastPerson07_generate(
                template_path=str(template_path) if template_path else None,
                title=title
            )
            
            logger.info(f"✅ Banner created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Banner creation error: {e}", exc_info=True)
            raise
