import asyncio
import io
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path
from loguru import logger
from config import config
from utils.anime_api import anime_api  # ✅ Anime integration

class LastPerson07_BannerEngine:
    """🎨 Professional banner generation engine"""
    
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
        Generate professional HD banner with anime wallpaper fallback
        
        Args:
            template_path: Path to template image (your 4 samples)
            title: Banner title text
            
        Returns:
            Path to generated banner image
        """
        try:
            logger.info(f"🎨 Generating banner: '{title}'")
            
            # ===== 1. BACKGROUND LOADING =====
            bg = await self._load_background(template_path)
            
            # ===== 2. DARK OVERLAY =====
            bg = self._apply_overlay(bg)
            
            # ===== 3. PROFESSIONAL TEXT =====
            draw = ImageDraw.Draw(bg)
            font_main, font_small = self._load_fonts()
            
            # Center main title
            text = title[:config.MAX_TITLE_LENGTH]
            x, y = self._calculate_text_position(draw, text, font_main)
            
            # 🔥 GLOW + STROKE EFFECT
            self._draw_glow_text(draw, text, (x, y), font_main)
            
            # Watermark
            self._draw_watermark(draw, font_small)
            
            # ===== 4. EXPORT =====
            output_path = await self._export_image(bg)
            
            logger.info(f"✅ Banner generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Generation FAILED: {e}", exc_info=True)
            raise Exception(f"Banner generation failed: {str(e)}")
    
    async def _load_background(self, template_path: str = None) -> Image.Image:
        """Load background: Template → Anime → Gradient"""
        try:
            # 1️⃣ PRIORITY: User's template (your 4 images)
            if template_path and Path(template_path).exists():
                bg = Image.open(template_path).convert("RGB")
                bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
                logger.info(f"✅ Template loaded: {template_path}")
                return bg
            
            # 2️⃣ FALLBACK: Real anime wallpaper
            logger.info("🎌 Fetching anime wallpaper...")
            wallpaper_data = await anime_api.get_anime_wallpaper()
            if wallpaper_data:
                bg = Image.open(io.BytesIO(wallpaper_data)).convert("RGB")
                bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
                logger.info("✅ Anime wallpaper loaded")
                return bg
            
            # 3️⃣ FINAL: Gradient fallback
            logger.warning("⚠️ Using gradient fallback")
            return self._create_gradient_bg()
            
        except Exception as e:
            logger.error(f"❌ Background load failed: {e}")
            return self._create_gradient_bg()
    
    def _apply_overlay(self, bg: Image.Image) -> Image.Image:
        """Apply dark overlay for text readability"""
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 140))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        return bg
    
    def _load_fonts(self):
        """Load professional fonts with fallbacks"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Arial Bold.ttf"  # macOS
        ]
        
        # Main font (80px)
        font_main = None
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    font_main = ImageFont.truetype(font_path, 80)
                    break
            except:
                continue
        
        # Small font (36px)
        font_small = None
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    font_small = ImageFont.truetype(font_path, 36)
                    break
            except:
                continue
        
        # Ultimate fallback
        if not font_main:
            font_main = ImageFont.load_default()
        if not font_small:
            font_small = ImageFont.load_default()
        
        logger.info("✅ Fonts loaded")
        return font_main, font_small
    
    def _calculate_text_position(self, draw: ImageDraw.ImageDraw, text: str, font) -> tuple:
        """Calculate centered text position"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2 - 60  # Vertical center + offset
        
        return x, y
    
    def _draw_glow_text(self, draw: ImageDraw.ImageDraw, text: str, pos: tuple, font):
        """Draw text with 🔥 GLOW + STROKE effect"""
        x, y = pos
        
        # 1. GLOW LAYERS (blue-ish glow)
        for glow_size in range(8, 0, -2):
            alpha = 60 + (8 - glow_size) * 15
            glow_color = (100, 150, 255, alpha)  # Blue glow
            
            for adj_x in [-glow_size//2, glow_size//2]:
                for adj_y in [-glow_size//2, glow_size//2]:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=glow_color[:3])
        
        # 2. BLACK STROKE (professional outline)
        for adj_x in range(-3, 4):
            for adj_y in range(-3, 4):
                if adj_x * adj_x + adj_y * adj_y <= 9:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=(0, 0, 0))
        
        # 3. MAIN TEXT (pure white)
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    def _draw_watermark(self, draw: ImageDraw.ImageDraw, font):
        """Draw professional watermark"""
        watermark = "@LastPerson07"
        draw.text((25, 25), watermark, font=font, fill=(180, 180, 180))
    
    def _create_gradient_bg(self) -> Image.Image:
        """Create beautiful gradient fallback"""
        # Dark purple-blue gradient
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        for i in range(self.height):
            r = int(20 + (i / self.height) * 40)
            g = int(15 + (i / self.height) * 25)
            b = int(40 + (i / self.height) * 80)
            color = (r, g, b)
            draw.line([(0, i), (self.width, i)], fill=color)
        
        return img
    
    async def _export_image(self, image: Image.Image) -> str:
        """Export with cleanup & optimization"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False,
            dir="/tmp"
        )
        output_path = temp_file.name
        temp_file.close()
        
        # Optimize & save
        image.save(
            output_path, 
            "JPEG", 
            quality=self.quality,
            optimize=True,
            progressive=True
        )
        
        # Cleanup old files (keep last 50)
        self._cleanup_temp_files()
        
        return output_path
    
    def _cleanup_temp_files(self):
        """Clean old temporary files"""
        try:
            temp_dir = Path("/tmp")
            banner_files = [
                f for f in temp_dir.iterdir() 
                if f.suffix == ".jpg" and f.name.startswith("tmp")
            ]
            
            if len(banner_files) > 50:
                banner_files.sort(key=lambda x: x.stat().st_mtime)
                for old_file in banner_files[:-50]:
                    try:
                        old_file.unlink()
                    except:
                        pass
        except:
            pass  # Silent fail for cleanup

# Global instance for easy import
banner_engine = LastPerson07_BannerEngine()
