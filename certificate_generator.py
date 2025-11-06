import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io


class CertificateGenerator:
    def __init__(self, certificate_template_path, output_dir):
        """Initialize the certificate generator"""
        self.template_path = certificate_template_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_certificate(self, name):
        """Generate a certificate PDF for a given name"""
        img = Image.open(self.template_path)
        width, height = img.size

        draw = ImageDraw.Draw(img)

        name_y_position = int(height * 0.50)

        font_size = 200
        try:
            font_path = "AlexBrush-Regular.ttf"
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                print(f"Loaded AlexBrush font successfully")
            else:
                print(f"Warning: AlexBrush-Regular.ttf not found, using fallback font")
                font_paths = [
                    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                    "/Library/Fonts/Times New Roman.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
                    "C:\\Windows\\Fonts\\times.ttf",
                ]
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, font_size)
                        break
                if font is None:
                    font = ImageFont.load_default()
        except Exception as e:
            print(f"Warning: Could not load custom font, using default. Error: {e}")
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        name_x_position = (width - text_width) // 2

        text_color = (123, 94, 210)
        stroke_width = 2
        draw.text((name_x_position, name_y_position), name, fill=text_color, font=font, stroke_width=stroke_width, stroke_fill=text_color)

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=95)
        img_buffer.seek(0)

        sanitized_name = "".join(
            c for c in name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        sanitized_name = sanitized_name.replace(" ", "_")
        pdf_filename = f"{sanitized_name}_certificate.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        img_aspect = width / height
        pdf_width = 11 * 72
        pdf_height = pdf_width / img_aspect

        c = canvas.Canvas(pdf_path, pagesize=(pdf_width, pdf_height))

        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=pdf_width, height=pdf_height)

        c.save()

        print(f"Generated certificate for {name}: {pdf_path}")
        return pdf_path
