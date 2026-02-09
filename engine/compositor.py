from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from loguru import logger
from typing import Tuple


class LastPerson07_Compositor:
    """
    Professional Image Compositor

    Features:
    ✔ Contrast tuning
    ✔ Cinematic color grading
    ✔ Dark gradient overlay
    ✔ Blur panel behind text
    ✔ Vignette
    ✔ Sharpness boost
    """

    # ---------------- MASTER COMPOSITE ---------------- #

    @staticmethod
    def composite(background: Image.Image) -> Image.Image:
        """
        Apply full cinematic pipeline.
        Safe to call inside asyncio.to_thread().
        """

        try:
            img = background.convert("RGB")

            img = LastPerson07_Compositor._contrast(img)
            img = LastPerson07_Compositor._color_grade(img)
            img = LastPerson07_Compositor._sharpness(img)
            img = LastPerson07_Compositor._gradient_overlay(img)
            img = LastPerson07_Compositor._vignette(img)

            return img

        except Exception as e:
            logger.exception(f"Compositing error: {e}")
            return background

    # ---------------- CONTRAST ---------------- #

    @staticmethod
    def _contrast(img: Image.Image, level: float = 1.25) -> Image.Image:
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(level)

    # ---------------- COLOR GRADE ---------------- #

    @staticmethod
    def _color_grade(img: Image.Image) -> Image.Image:
        """
        Slight saturation boost for anime colors.
        """
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)

        brightness = ImageEnhance.Brightness(img)
        img = brightness.enhance(1.05)

        return img

    # ---------------- SHARPNESS ---------------- #

    @staticmethod
    def _sharpness(img: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1.2)

    # ---------------- GRADIENT OVERLAY ---------------- #

    @staticmethod
    def _gradient_overlay(img: Image.Image) -> Image.Image:
        """
        Adds dark bottom gradient.
        Makes text MUCH more readable.
        """

        width, height = img.size

        gradient = Image.new("L", (1, height))

        for y in range(height):
            # darker at bottom
            value = int(255 * (y / height) ** 2)
            gradient.putpixel((0, y), value)

        alpha = gradient.resize((width, height))

        black_img = Image.new("RGBA", (width, height), (0, 0, 0, 180))
        alpha_mask = Image.merge("RGBA", (alpha, alpha, alpha, alpha))

        gradient_layer = Image.composite(
            black_img,
            Image.new("RGBA", (width, height), (0, 0, 0, 0)),
            alpha
        )

        return Image.alpha_composite(img.convert("RGBA"), gradient_layer).convert("RGB")

    # ---------------- BLUR PANEL ---------------- #

    @staticmethod
    def blur_panel(
        img: Image.Image,
        box: Tuple[int, int, int, int],
        blur_radius: int = 18
    ) -> Image.Image:
        """
        Creates a blurred rectangle behind text.
        Netflix-style readability.
        """

        try:
            region = img.crop(box).filter(
                ImageFilter.GaussianBlur(blur_radius)
            )

            img.paste(region, box)

            # optional dark overlay
            draw = ImageDraw.Draw(img, "RGBA")
            draw.rectangle(box, fill=(0, 0, 0, 90))

            return img

        except Exception as e:
            logger.error(f"Blur panel error: {e}")
            return img

    # ---------------- VIGNETTE ---------------- #

    @staticmethod
    def _vignette(img: Image.Image) -> Image.Image:
        """
        Cinematic edge darkening.
        Very subtle but high-end look.
        """

        width, height = img.size

        vignette = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(vignette)

        max_radius = max(width, height)

        for i in range(0, max_radius, 8):
            alpha = int(255 * (i / max_radius) ** 2)
            draw.ellipse(
                (-i, -i, width + i, height + i),
                outline=alpha
            )

        vignette = vignette.filter(ImageFilter.GaussianBlur(80))

        black = Image.new("RGBA", (width, height), (0, 0, 0, 140))

        return Image.composite(
            img.convert("RGBA"),
            black,
            vignette
        ).convert("RGB")
