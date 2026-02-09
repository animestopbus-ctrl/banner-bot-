from PIL import ImageDraw, ImageFont, ImageFilter, Image
from loguru import logger
from typing import Tuple


class LastPerson07_Typography:
    """
    Professional typography helper.

    Features:
    ✔ Native stroke (FAST)
    ✔ Glow support
    ✔ Multiline wrapping
    ✔ Auto font scaling
    ✔ Center positioning
    """

    # ---------------- AUTO WRAP ---------------- #

    @staticmethod
    def wrap_text(draw, text, font, max_width):
        """
        Automatically wrap text into multiple lines
        so it never overflows the banner.
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)

            if bbox[2] <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    # ---------------- AUTO SCALE ---------------- #

    @staticmethod
    def auto_font(draw, text, font_path, start_size, max_width):
        """
        Shrinks font until text fits.
        """
        size = start_size

        while size > 20:
            font = ImageFont.truetype(font_path, size)
            bbox = draw.multiline_textbbox((0, 0), text, font=font)

            if bbox[2] <= max_width:
                return font

            size -= 4

        return ImageFont.truetype(font_path, 20)

    # ---------------- CENTER POSITION ---------------- #

    @staticmethod
    def center_position(draw, text, font, canvas_width, canvas_height, y_offset=0):
        bbox = draw.multiline_textbbox((0, 0), text, font=font)

        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (canvas_width - text_w) // 2
        y = (canvas_height - text_h) // 2 + y_offset

        return x, y

    # ---------------- GLOW ---------------- #

    @staticmethod
    def draw_glow_text(
        image: Image.Image,
        position: Tuple[int, int],
        text: str,
        font,
        glow_radius: int = 12,
        glow_color=(120, 160, 255),
        stroke_width: int = 3
    ):
        """
        Draw BEAUTIFUL glow using blurred layer.
        MUCH better than manual loops.
        """

        try:
            if image.mode != "RGBA":
                base = image.convert("RGBA")
            else:
                base = image

            glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)

            # draw glow text
            glow_draw.multiline_text(
                position,
                text,
                font=font,
                fill=(*glow_color, 180),
                align="center"
            )

            # blur glow
            glow_layer = glow_layer.filter(
                ImageFilter.GaussianBlur(glow_radius)
            )

            base = Image.alpha_composite(base, glow_layer)

            # draw final text with stroke
            final_draw = ImageDraw.Draw(base)

            final_draw.multiline_text(
                position,
                text,
                font=font,
                fill=(255, 255, 255),
                stroke_width=stroke_width,
                stroke_fill=(0, 0, 0),
                align="center"
            )

            return base.convert("RGB")

        except Exception as e:
            logger.error(f"Glow typography error: {e}")
            return image

    # ---------------- SIMPLE TEXT ---------------- #

    @staticmethod
    def draw_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font,
        position: tuple,
        stroke_width: int = 3,
        stroke_color: tuple = (0, 0, 0),
        fill_color: tuple = (255, 255, 255),
    ):
        """
        Fast stroke text using Pillow native support.
        """

        try:
            draw.multiline_text(
                position,
                text,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
                align="center"
            )

        except Exception as e:
            logger.error(f"Typography error: {e}")
