from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from loguru import logger

class LastPerson07_Compositor:
    """Image composition & layering"""
    
    @staticmethod
    def LastPerson07_composite(background: Image.Image) -> Image.Image:
        """Apply compositing effects"""
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(background)
            background = enhancer.enhance(1.2)
            
            return background
            
        except Exception as e:
            logger.error(f"Compositing error: {e}")
            return background
