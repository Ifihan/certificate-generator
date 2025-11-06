import os
import csv
from flask import Flask, render_template, jsonify, send_file
from certificate_generator import CertificateGenerator
from pdf_uploader import PDFUploader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CERTIFICATE_IMAGE = 'certificate.jpg'
NAMES_CSV = 'names.csv'
OUTPUT_DIR = 'output'
GENERATED_CSV = 'generated_certificates.csv'

UPLOAD_SERVICE = os.getenv('UPLOAD_SERVICE', 'cloudinary')

CLOUDINARY_CONFIG = {
    'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'api_key': os.getenv('CLOUDINARY_API_KEY'),
    'api_secret': os.getenv('CLOUDINARY_API_SECRET')
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_certificates():
    """Generate all certificates and upload them"""
    try:
        names = []
        with open(NAMES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                names.append(row['name'].strip())

        generator = CertificateGenerator(CERTIFICATE_IMAGE, OUTPUT_DIR)

        if UPLOAD_SERVICE == 'cloudinary':
            uploader = PDFUploader(service='cloudinary', cloudinary_config=CLOUDINARY_CONFIG)
        else:
            uploader = PDFUploader(service=UPLOAD_SERVICE)

        results = []
        total = len(names)

        for index, name in enumerate(names, 1):
            try:
                pdf_path = generator.generate_certificate(name)
                url = uploader.upload(pdf_path, name)

                results.append({
                    'name': name,
                    'url': url,
                    'status': 'success'
                })

                print(f"Processed {index}/{total}: {name} -> {url}")

            except Exception as e:
                results.append({
                    'name': name,
                    'url': '',
                    'status': 'error',
                    'error': str(e)
                })
                print(f"Error processing {name}: {e}")

        with open(GENERATED_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'url', 'status'])
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'name': result['name'],
                    'url': result['url'],
                    'status': result['status']
                })

        return jsonify({
            'success': True,
            'message': f'Generated {len(results)} certificates',
            'results': results,
            'csv_file': GENERATED_CSV
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download-csv')
def download_csv():
    """Download the generated CSV file"""
    if os.path.exists(GENERATED_CSV):
        return send_file(GENERATED_CSV, as_attachment=True)
    else:
        return jsonify({'error': 'CSV file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
