# Certificate Generator

> A customizable, production-ready certificate generator that creates personalized certificates from CSV data and uploads them to cloud storage providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Visual Settings Panel**: Customize certificates directly in the browser with live preview
- **Drag-and-Drop Text Positioning**: Position text on certificates by dragging a marker
- **Multiple Storage Providers**: Choose from Cloudinary, Catbox, file.io, or tmpfiles
- **Progress Tracking**: Automatic progress saving - resume if interrupted
- **Cancel Generation**: Stop certificate generation mid-process and resume later
- **CSV Change Detection**: Detects when a different CSV is uploaded
- **Custom Templates & Fonts**: Upload your own certificate templates and fonts

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Ifihan/certificate-generator.git
   cd certificate-generator
   ```

2. **Install UV (if not already installed)**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**

   ```bash
   uv sync
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your storage provider credentials (see [Storage Provider Setup](#storage-provider-setup))

5. **Run the application**

   ```bash
   python app.py
   ```

   Or with UV:

   ```bash
   uv run python app.py
   ```

6. **Open your browser**
   Navigate to [http://localhost:5001](http://localhost:5001)

## Usage

### Basic Workflow

1. **Customize Settings**: Expand "Certificate Settings" to upload your template, adjust template, font, colors, and text position
2. **Upload CSV File**: Drag and drop a CSV file or click "Browse Files" to select your CSV
3. **Generate Certificates**: Click "Generate Certificates" to start processing
4. **Download Results**: Download the CSV with certificate URLs when complete

### CSV Format

Your CSV file must contain a `name` column:

```csv
name,email,department
John Doe,john@example.com,Engineering
Jane Smith,jane@example.com,Marketing
```

All columns will be preserved in the output CSV:

```csv
name,email,department,url,status
John Doe,john@example.com,Engineering,https://...,success
Jane Smith,jane@example.com,Marketing,https://...,success
```

### Resume Functionality

If certificate generation is interrupted:

1. Reopen the application
2. The system detects previous progress automatically
3. Click "Continue Generation" to resume from where you left off

### Changing CSVs

If you upload a different CSV:

1. The system detects the change
2. You'll be prompted to reset progress
3. Click "Start Fresh" to clear old data and use the new CSV

## Customization

### Visual Settings (Web Interface)

The easiest way to customize certificates is through the web interface:

1. Click on "Certificate Settings" to expand the settings panel
2. **Template**: Select or upload a certificate template image (PNG/JPG)
3. **Font**: Select or upload a custom font file (TTF/OTF)
4. **Font Size**: Adjust using the slider (20-300px)
5. **Text Color**: Pick a color using the color picker
6. **Stroke Width**: Adjust text stroke/outline thickness (0-10px)
7. **Text Position**: Drag the marker on the preview to position text
8. Click "Save Settings" to persist your changes

Settings are saved to `settings.json` and persist across sessions.

### Configuration File

Advanced settings can be configured in [`config.py`](./config.py):

```python
# CSV Settings
NAME_COLUMN = 'name'  # Required column name for recipient names

# Storage Provider (cloudinary|catbox|fileio|tmpfiles)
UPLOAD_SERVICE = os.getenv("UPLOAD_SERVICE", "cloudinary")

# App Settings
DEBUG_MODE = True
PORT = 5000
HOST = "127.0.0.1"
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
```

### Storage Provider Setup

Edit your [`.env`](./.env) file:

```env
# Choose your storage provider
UPLOAD_SERVICE=cloudinary  # Options: cloudinary, catbox, fileio, tmpfiles

# Cloudinary Configuration (only if using cloudinary)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_FOLDER=demo  # Optional: folder name in Cloudinary (default: demo)
```

#### Storage Provider Comparison

| Provider       | Storage Duration | Requires Auth | Free Tier | CDN |
| -------------- | ---------------- | ------------- | --------- | --- |
| **Cloudinary** | Permanent        | Yes           | 25GB      | Yes |
| **Catbox**     | Permanent        | No            | Unlimited | Yes |
| **file.io**    | 1 year           | No            | Unlimited | No  |
| **tmpfiles**   | Temporary        | No            | Unlimited | No  |

**Recommended**: Cloudinary for production (professional CDN, permanent storage)

#### Setting up Cloudinary

1. Create a free account at [cloudinary.com](https://cloudinary.com)
2. Go to Dashboard → Account Details
3. Copy your Cloud Name, API Key, and API Secret
4. Add them to your `.env` file

#### Using Other Providers

For Catbox, file.io, or tmpfiles - no credentials needed:

```env
UPLOAD_SERVICE=catbox
```

## Project Structure

```bash
certificate-generator/
├── app.py                      # Flask application with all routes
├── certificate_generator.py    # Certificate generation logic
├── pdf_uploader.py            # Multi-provider upload abstraction
├── config.py                  # Central configuration file
├── settings.json              # Saved visual settings (auto-generated)
├── templates/
│   └── index.html             # Web interface
├── static/
│   ├── css/
│   │   └── main.css           # Application styles
│   ├── js/
│   │   └── main.js            # Frontend logic
│   ├── fonts/                 # Font files (TTF/OTF)
│   │   └── AlexBrush-Regular.ttf
│   └── templates/             # Certificate template images (PNG/JPG)
│       └── certificate.png
├── output/                    # Generated certificate PDFs
├── uploads/                   # Uploaded CSV files
├── generated_certificates.csv # Results with certificate URLs
├── .env                       # Environment variables
├── .env.example              # Environment template
├── pyproject.toml            # Dependencies
└── README.md                 # This file
```

## API Endpoints

### Core Endpoints

| Endpoint             | Method | Description                           |
| -------------------- | ------ | ------------------------------------- |
| `/`                  | GET    | Render main page                      |
| `/upload-csv`        | POST   | Upload and validate CSV file          |
| `/check-progress`    | GET    | Check for existing progress           |
| `/generate`          | POST   | Generate certificates                 |
| `/cancel-generation` | POST   | Cancel ongoing certificate generation |
| `/reset-progress`    | POST   | Reset progress for new CSV            |
| `/download-csv`      | GET    | Download results CSV                  |

### Settings API

| Endpoint               | Method | Description                          |
| ---------------------- | ------ | ------------------------------------ |
| `/api/settings`        | GET    | Get current visual settings          |
| `/api/settings`        | POST   | Save visual settings                 |
| `/api/templates`       | GET    | List available certificate templates |
| `/api/fonts`           | GET    | List available fonts                 |
| `/api/upload-template` | POST   | Upload a new certificate template    |
| `/api/upload-font`     | POST   | Upload a new font file               |
| `/api/preview`         | POST   | Generate a preview image             |

## Development

### Running in Development Mode

```bash
# Activate virtual environment (if using uv)
source .venv/bin/activate

# Run with debug mode
python app.py
```

## Deployment

### Environment Variables

For production, set these environment variables:

```env
DEBUG=False
HOST=0.0.0.0
PORT=5000
UPLOAD_SERVICE=cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Deploying to Render/Heroku/Railway

1. Push your code to GitHub
2. Connect your repository to your platform
3. Set environment variables in platform dashboard
4. Deploy!

## Troubleshooting

### Font Issues

If custom font doesn't load:

- Upload a font through the web interface or place it in `static/fonts/`
- Ensure font file is in TTF or OTF format
- System will automatically fall back to system fonts if the selected font is unavailable

### CSV Upload Errors

- Ensure CSV has a `name` column
- Check CSV is properly formatted (UTF-8 encoding)
- File size limit: 16MB (configurable in `config.py`)

### Storage Provider Errors

- **Cloudinary**: Verify credentials in `.env`
- **Others**: Check network connection
- Review error messages in browser console

### Progress Not Saving

- Check write permissions for `generated_certificates.csv`
- Ensure `uploads/` and `output/` directories exist
- Check browser console for errors

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Ifihan/certificate-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ifihan/certificate-generator/discussions)

## Acknowledgments

- Built with Flask, Pillow, HTML, CSS, and JavaScript.

---

Made with ❤️ for easy certificate generation
