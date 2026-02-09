from PIL import ImageDraw, ImageFont
from loguru import logger

class LastPerson07_Typography:
    """Typography & text rendering"""
    
    @staticmethod
    def LastPerson07_apply_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        position: tuple,
        stroke_width: int = 4,
        stroke_color: tuple = (0, 0, 0),
        fill_color: tuple = (255, 255, 255)
    ):
        """Draw text with stroke"""
        try:
            x, y = position
            
            # Draw stroke
            for adj_x in range(-stroke_width, stroke_width + 1):
                for adj_y in range(-stroke_width, stroke_width + 1):
                    if adj_x * adj_x + adj_y * adj_y <= stroke_width * stroke_width:
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
            
            # Draw main text
            draw.text(position, text, font=font, fill=fill_color)
            
        except Exception as e:
            logger.error(f"Typography error: {e}")
