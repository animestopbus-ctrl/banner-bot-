from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import tempfile
from pathlib import Path
from loguru import logger
from config import config

class LastPerson07_BannerEngine:
    """Professional banner generation engine"""
    
    def __init__(self):
        self.width = config.BANNER_WIDTH
        self.height = config.BANNER_HEIGHT
        self.quality = config.BANNER_QUALITY
    
    async def LastPerson07_generate(
        self,
        template_path: str = None,
        title: str = ""
    ) -> str:
        """
        Generate a professional banner
        
        Args:
            template_path: Path to template image
            title: Banner title text
        
        Returns:
            Path to generated banner
        """
        try:
            logger.info(f"🎨 Generating banner: {title}")
            
            # Load or create background
            if template_path and Path(template_path).exists():
                try:
                    bg = Image.open(template_path).convert("RGB")
                    bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
                    logger.info(f"✅ Template loaded: {template_path}")
                except Exception as e:
                    logger.warning(f"Template load failed: {e}")
                    bg = Image.new("RGB", (self.width, self.height), (0, 0, 0))
            else:
                bg = Image.new("RGB", (self.width, self.height), (0, 0, 0))
            
            # Add dark overlay for text readability
            overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 120))
            bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
            
            # Draw text
            draw = ImageDraw.Draw(bg)
            
            # Load fonts
            try:
                font_size = 80
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    font_size
                )
                small_font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    40
                )
            except Exception as e:
                logger.warning(f"Font loading failed: {e}")
                font = ImageFont.load_default()
                small_font = font
            
            # Draw main title with stroke
            text = title[:60]
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            
            # Draw stroke (black outline)
            for adj_x in range(-4, 5):
                for adj_y in range(-4, 5):
                    if adj_x * adj_x + adj_y * adj_y <= 16:
                        draw.text(
                            (x + adj_x, y + adj_y),
                            text,
                            font=font,
                            fill=(0, 0, 0)
                        )
            
            # Draw main text (white)
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
            
            # Draw watermark
            watermark = "@LastPerson07"
            draw.text((20, 20), watermark, font=small_font, fill=(150, 150, 150))
            
            # Save to temporary file
            output_path = tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False,
                dir="/tmp"
            ).name
            
            bg.save(output_path, "JPEG", quality=self.quality)
            logger.info(f"✅ Banner saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise
