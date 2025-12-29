"""Certificate Generator Configuration - Customize your settings here"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Settings File
SETTINGS_FILE = "settings.json"
TEMPLATES_DIR = "static/templates"
FONTS_DIR = "static/fonts"

# Default Visual Settings
DEFAULT_VISUAL_SETTINGS = {
    "template": "certificate.png",
    "font_path": "static/fonts/AlexBrush-Regular.ttf",
    "font_size": 120,
    "text_x_position": 0.5,
    "text_y_position": 0.44,
    "text_color": [123, 94, 210],
    "stroke_width": 2,
    "image_quality": 95
}


def load_settings():
    """Load visual settings from JSON file, or return defaults"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_VISUAL_SETTINGS, **settings}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_VISUAL_SETTINGS.copy()


def save_settings(settings):
    """Save visual settings to JSON file"""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# Load current settings for backward compatibility
_settings = load_settings()
CERTIFICATE_TEMPLATE = os.path.join(TEMPLATES_DIR, _settings["template"])
FONT_PATH = _settings["font_path"]
FONT_SIZE = _settings["font_size"]
TEXT_Y_POSITION = _settings["text_y_position"]
TEXT_COLOR = tuple(_settings["text_color"])
STROKE_WIDTH = _settings["stroke_width"]
IMAGE_QUALITY = _settings["image_quality"]

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
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "demo")

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

    settings = load_settings()
    template_path = os.path.join(TEMPLATES_DIR, settings["template"])

    if not os.path.exists(template_path):
        errors.append(f"Certificate template not found: {template_path}")
        errors.append(
            f"  Please add a certificate template image (PNG/JPG) in static/templates/"
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
