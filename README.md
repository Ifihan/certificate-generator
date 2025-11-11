# Certificate Generator

> A customizable, production-ready certificate generator that creates personalized certificates from CSV data and uploads them to cloud storage providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **CSV Upload Interface**: Upload CSV files directly through a web interface
- **Multiple Storage Providers**: Choose from Cloudinary, Catbox, file.io, or tmpfiles
- **Progress Tracking**: Automatic progress saving - resume if interrupted
- **CSV Change Detection**: Detects when a different CSV is uploaded
- **Column Preservation**: All columns from input CSV are preserved in output
- **Beautiful Certificates**: Customizable fonts, colors, and positioning
- **Easy Customization**: Single configuration file for all settings
- **Production Ready**: Error handling, validation, and robust architecture

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd icair-certificate
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
   ./start.sh
   ```

   Or manually:

   ```bash
   uv run python app.py
   ```

6. **Open your browser**
   Navigate to [http://localhost:5000](http://localhost:5000)

## Usage

### Basic Workflow

1. **Upload CSV File**: Click "Choose CSV File" and select your CSV
2. **Generate Certificates**: Click "Generate Certificates" to start processing
3. **Download Results**: Download the CSV with certificate URLs when complete

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

All customization is done through [`config.py`](./config.py):

### Visual Customization

```python
# Certificate Template
CERTIFICATE_TEMPLATE = 'certificate.jpg'  # Path to your template image

# Font Settings
FONT_PATH = 'AlexBrush-Regular.ttf'       # Path to your font file
FONT_SIZE = 200                            # Font size for names

# Text Positioning (0.0 = top, 0.5 = middle, 1.0 = bottom)
TEXT_Y_POSITION = 0.50

# Text Color (RGB: 0-255)
TEXT_COLOR = (123, 94, 210)               # Purple

# Text Stroke
STROKE_WIDTH = 2
```

### Branding Customization

```python
# Application Name (shown in UI)
APP_NAME = "ICAIR Certificate Generator"

# Application Subtitle
APP_SUBTITLE = "Generate participation certificates for all attendees"

# UI Color Scheme (CSS gradient colors)
PRIMARY_COLOR = "#667eea"    # Purple
SECONDARY_COLOR = "#764ba2"  # Darker purple
```

### CSV Configuration

```python
# Required column name for recipient names
NAME_COLUMN = 'name'

# Additional columns to preserve in output CSV
PRESERVE_COLUMNS = []  # All columns are preserved by default
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
icair-certificate/
├── app.py                      # Flask application with all routes
├── certificate_generator.py    # Certificate generation logic
├── pdf_uploader.py            # Multi-provider upload abstraction
├── config.py                  # Central configuration file
├── templates/
│   └── index.html             # Web interface
├── certificate.jpg            # Certificate template (replace with yours)
├── AlexBrush-Regular.ttf     # Font file (replace with yours)
├── output/                    # Generated PDFs
├── uploads/                   # Uploaded CSV files
├── generated_certificates.csv # Results with URLs
├── progress.json              # Progress tracking
├── .env                       # Environment variables (create from .env.example)
├── .env.example              # Environment template
├── pyproject.toml            # Dependencies
└── README.md                 # This file
```

## API Endpoints

| Endpoint          | Method | Description                  |
| ----------------- | ------ | ---------------------------- |
| `/`               | GET    | Render main page             |
| `/upload-csv`     | POST   | Upload and validate CSV file |
| `/check-progress` | GET    | Check for existing progress  |
| `/generate`       | POST   | Generate certificates        |
| `/reset-progress` | POST   | Reset progress for new CSV   |
| `/download-csv`   | GET    | Download results CSV         |

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

- Ensure font file exists in project root
- Check `FONT_PATH` in `config.py`
- System will automatically fall back to system fonts

### CSV Upload Errors

- Ensure CSV has a `name` column
- Check CSV is properly formatted (UTF-8 encoding)
- File size limit: 16MB (configurable in `config.py`)

### Storage Provider Errors

- **Cloudinary**: Verify credentials in `.env`
- **Others**: Check network connection
- Review error messages in browser console

### Progress Not Saving

- Check write permissions for `progress.json`
- Ensure `uploads/` directory exists
- Check browser console for errors

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/icair-certificate/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/icair-certificate/discussions)

## Acknowledgments

- Built with Flask, Pillow, and ReportLab
- Storage provided by Cloudinary, Catbox, file.io, and tmpfiles
- Font: Alex Brush by TypeSETit

---

Made with ❤️ for easy certificate generation
