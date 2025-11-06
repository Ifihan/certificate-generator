# ICAIR Certificate Generator

Automatically generate participation certificates for ICAIR 2025 attendees with their names and upload them to get shareable links.

## Features

- Reads names from a CSV file
- Generates personalized certificates (PDF format) with **AlexBrush font** in **purple**
- Uploads PDFs to **Cloudinary** (or other free hosting services)
- Returns permanent shareable links for each certificate
- Exports results to a CSV file with names and links
- Simple web interface with a single "Generate" button

## Setup

### Prerequisites

- Python 3.11+ (managed by UV)
- UV package manager installed
- Cloudinary account (free tier) - [Sign up here](https://cloudinary.com/users/register_free)

### Installation

1. **Set up Cloudinary** (Recommended):
   ```bash
   # Copy the environment template
   cp .env.example .env

   # Edit .env and add your Cloudinary credentials
   # Get credentials from: https://cloudinary.com/console
   ```

   See [CLOUDINARY_SETUP.md](CLOUDINARY_SETUP.md) for detailed instructions.

2. **Run the application**:
   ```bash
   # Easy way - use the start script
   ./start.sh
   ```

   Or manually:
   ```bash
   # Run with UV (recommended)
   uv run app.py

   # Or activate venv first
   source .venv/bin/activate
   python app.py
   ```

3. Open your browser and navigate to: http://localhost:5000

## Usage

1. Ensure your names.csv file is in the project root
2. Ensure your certificate.jpg template is in the project root
3. Open the web interface at http://localhost:5000
4. Click "Generate All Certificates"
5. Wait for completion
6. Download the CSV with all names and links

## Upload Services

The app supports multiple free file hosting services:

1. **Cloudinary** (Default - Recommended)
   - Permanent storage, no expiry
   - 25GB free tier
   - Fast CDN delivery
   - Requires free account setup

2. **catbox.moe** - Permanent, no account needed
3. **file.io** - 1-year storage, no account needed
4. **tmpfiles.org** - Temporary storage, no account needed

To change the service, edit the `UPLOAD_SERVICE` variable in your `.env` file:
```bash
UPLOAD_SERVICE=cloudinary  # or catbox, fileio, tmpfiles
```

## Certificate Customization

The certificates use:
- **Font**: AlexBrush-Regular.ttf (script font)
- **Color**: Purple (#7B5ED2) matching ICAIR branding
- **Position**: Centered below "is hereby granted to"

To modify these settings, edit [certificate_generator.py](certificate_generator.py).

## License

This project is for ICAIR 2025 internal use.
