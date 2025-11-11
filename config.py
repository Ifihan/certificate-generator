"""Certificate Generator Configuration - Customize your settings here"""

import os
from dotenv import load_dotenv

load_dotenv()

# Visual Settings
CERTIFICATE_TEMPLATE = 'certificate.jpg'
FONT_PATH = 'AlexBrush-Regular.ttf'
FONT_SIZE = 200
TEXT_Y_POSITION = 0.50  # 0.0=top, 0.5=middle, 1.0=bottom
TEXT_COLOR = (123, 94, 210)  # RGB purple
STROKE_WIDTH = 2
IMAGE_QUALITY = 95

# Branding
APP_NAME = "Certificate Generator"
APP_SUBTITLE = "Generate and distribute certificates with ease"
PRIMARY_COLOR = "#667eea"
SECONDARY_COLOR = "#764ba2"

# File Paths
OUTPUT_DIR = 'output'
UPLOAD_DIR = 'uploads'
GENERATED_CSV = 'generated_certificates.csv'

# CSV Settings
NAME_COLUMN = 'name'

# Storage Provider (cloudinary|catbox|fileio|tmpfiles)
UPLOAD_SERVICE = os.getenv('UPLOAD_SERVICE', 'cloudinary')
CLOUDINARY_CONFIG = {
    'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'api_key': os.getenv('CLOUDINARY_API_KEY'),
    'api_secret': os.getenv('CLOUDINARY_API_SECRET')
}

# App Settings
DEBUG_MODE = os.getenv('DEBUG', 'True').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '127.0.0.1')
MAX_UPLOAD_SIZE = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'csv'}

# Fallback Fonts
FALLBACK_FONTS = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Times New Roman.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "C:\\Windows\\Fonts\\times.ttf",
]

# Helpers
def get_cloudinary_config():
    if UPLOAD_SERVICE == 'cloudinary' and not all(CLOUDINARY_CONFIG.values()):
        raise ValueError("Cloudinary credentials not configured in .env file")
    return CLOUDINARY_CONFIG if UPLOAD_SERVICE == 'cloudinary' else None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Setup directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
