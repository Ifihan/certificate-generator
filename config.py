"""Certificate Generator Configuration - Customize your settings here"""

import os
from dotenv import load_dotenv

load_dotenv()

# Visual Settings
CERTIFICATE_TEMPLATE = "certificate.png"
FONT_PATH = "static/fonts/AlexBrush-Regular.ttf"
FONT_SIZE = 120
TEXT_Y_POSITION = 0.44
TEXT_COLOR = (123, 94, 210)
STROKE_WIDTH = 2
IMAGE_QUALITY = 95

# File Paths
OUTPUT_DIR = "output"
UPLOAD_DIR = "uploads"
GENERATED_CSV = "generated_certificates.csv"

# CSV Settings
NAME_COLUMN = "name"

# Storage Provider (cloudinary|catbox|fileio|tmpfiles)
UPLOAD_SERVICE = os.getenv("UPLOAD_SERVICE", "cloudinary")
CLOUDINARY_CONFIG = {
    "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "api_key": os.getenv("CLOUDINARY_API_KEY"),
    "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
}

# App Settings
DEBUG_MODE = os.getenv("DEBUG", "True").lower() == "true"
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "127.0.0.1")
MAX_UPLOAD_SIZE = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv"}

# Fallback Fonts
FALLBACK_FONTS = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Times New Roman.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "C:\\Windows\\Fonts\\times.ttf",
]


# Helpers
def get_cloudinary_config():
    if UPLOAD_SERVICE == "cloudinary" and not all(CLOUDINARY_CONFIG.values()):
        raise ValueError("Cloudinary credentials not configured in .env file")
    return CLOUDINARY_CONFIG if UPLOAD_SERVICE == "cloudinary" else None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Setup directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Validation
def validate_setup():
    """Validate that all required files and settings are present"""
    errors = []

    if not os.path.exists(CERTIFICATE_TEMPLATE):
        errors.append(f"Certificate template not found: {CERTIFICATE_TEMPLATE}")
        errors.append(
            f"  Please add a certificate template image (PNG/JPG) in the project root"
        )

    if UPLOAD_SERVICE == "cloudinary" and not all(CLOUDINARY_CONFIG.values()):
        errors.append("Cloudinary credentials missing in .env file")
        errors.append(
            "  Required: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET"
        )

    if errors:
        error_msg = "\n❌ Setup Validation Failed:\n" + "\n".join(
            f"  • {err}" for err in errors
        )
        raise ValueError(error_msg)

    return True
