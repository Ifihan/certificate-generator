import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import config


class CertificateGenerator:
    def __init__(self, settings=None):
        self.settings = settings or config.load_settings()
        self.output_dir = config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_template_path(self):
        return os.path.join(config.TEMPLATES_DIR, self.settings["template"])

    def _load_font(self):
        font_path = self.settings["font_path"]
        font_size = self.settings["font_size"]

        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)
        for path in config.FALLBACK_FONTS:
            if os.path.exists(path):
                return ImageFont.truetype(path, font_size)
        return ImageFont.load_default()

    def _convert_to_rgb(self, img):
        """Convert image to RGB mode for JPEG compatibility"""
        if img.mode in ("RGBA", "LA", "P"):
            # Create a white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            return background
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img

    def generate_certificate(self, name):
        template_path = self._get_template_path()

        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Certificate template not found: {template_path}\n"
                f"Please add a certificate template image to static/templates/."
            )

        img = Image.open(template_path)
        # Convert to RGB if necessary (for JPEG compatibility)
        img = self._convert_to_rgb(img)
        width, height = img.size
        draw = ImageDraw.Draw(img)
        font = self._load_font()

        # Get text positioning
        text_x_position = self.settings.get("text_x_position", 0.5)
        text_y_position = self.settings.get("text_y_position", 0.44)
        text_color = tuple(self.settings["text_color"])
        stroke_width = self.settings["stroke_width"]

        # Calculate text position
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Use x position (centered around the point)
        x = int(width * text_x_position) - text_width // 2
        y = int(height * text_y_position) - text_height // 2

        draw.text(
            (x, y), name, fill=text_color, font=font,
            stroke_width=stroke_width, stroke_fill=text_color
        )

        # Convert to PDF
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=self.settings["image_quality"])
        img_buffer.seek(0)

        sanitized = "".join(c if c.isalnum() or c in ("_", "-", " ") else "_" for c in name)
        sanitized = sanitized.replace(" ", "_").strip("_")
        pdf_path = os.path.join(self.output_dir, f"{sanitized}_certificate.pdf")

        pdf_width = 11 * 72
        pdf_height = pdf_width / (width / height)
        c = canvas.Canvas(pdf_path, pagesize=(pdf_width, pdf_height))
        c.drawImage(ImageReader(img_buffer), 0, 0, width=pdf_width, height=pdf_height)
        c.save()

        return pdf_path

    def generate_preview(self, name="Sample Name", settings=None):
        """Generate a preview image with the given settings, returns base64 encoded JPEG"""
        if settings:
            self.settings = {**self.settings, **settings}

        template_path = self._get_template_path()

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        img = Image.open(template_path)
        # Convert to RGB if necessary (for JPEG compatibility)
        img = self._convert_to_rgb(img)
        width, height = img.size
        draw = ImageDraw.Draw(img)
        font = self._load_font()

        # Get text positioning
        text_x_position = self.settings.get("text_x_position", 0.5)
        text_y_position = self.settings.get("text_y_position", 0.44)
        text_color = tuple(self.settings["text_color"])
        stroke_width = self.settings["stroke_width"]

        # Calculate text position
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = int(width * text_x_position) - text_width // 2
        y = int(height * text_y_position) - text_height // 2

        draw.text(
            (x, y), name, fill=text_color, font=font,
            stroke_width=stroke_width, stroke_fill=text_color
        )

        # Resize for preview (max 800px width)
        max_preview_width = 800
        if width > max_preview_width:
            ratio = max_preview_width / width
            new_size = (max_preview_width, int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/jpeg;base64,{base64_image}"
