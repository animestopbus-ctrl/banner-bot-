from PIL import Image
from loguru import logger
import os

class LastPerson07_Exporter:
    """Image export & optimization"""
    
    @staticmethod
    def LastPerson07_export(
        image: Image.Image,
        output_path: str,
        quality: int = 90
    ):
        """Export and optimize image"""
        try:
            image.save(output_path, "JPEG", quality=quality, optimize=True)
            logger.info(f"✅ Exported: {output_path}")
            
            # Cleanup old files
            try:
                files = [f for f in os.listdir("/tmp") if f.startswith("tmpvvk")]
                if len(files) > 100:
                    files.sort(key=lambda x: os.path.getctime(f"/tmp/{x}"))
                    for old_file in files[:-100]:
                        try:
                            os.remove(f"/tmp/{old_file}")
                        except:
                            pass
            except:
                pass
            
        except Exception as e:
            logger.error(f"Export error: {e}")
