import os
import io
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import config


class CertificateGenerator:
    def __init__(self, template_path=None, output_dir=None):
        self.template_path = template_path or config.CERTIFICATE_TEMPLATE
        self.output_dir = output_dir or config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_font(self):
        if os.path.exists(config.FONT_PATH):
            return ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE)
        for path in config.FALLBACK_FONTS:
            if os.path.exists(path):
                return ImageFont.truetype(path, config.FONT_SIZE)
        return ImageFont.load_default()

    def generate_certificate(self, name):
        img = Image.open(self.template_path)
        width, height = img.size
        draw = ImageDraw.Draw(img)
        font = self._load_font()

        # Center text
        bbox = draw.textbbox((0, 0), name, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        y = int(height * config.TEXT_Y_POSITION)

        draw.text((x, y), name, fill=config.TEXT_COLOR, font=font,
                  stroke_width=config.STROKE_WIDTH, stroke_fill=config.TEXT_COLOR)

        # Convert to PDF
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=config.IMAGE_QUALITY)
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
