import os
import csv
import hashlib
import logging
from threading import Lock
from flask import Flask, render_template, jsonify, send_file, request
from werkzeug.utils import secure_filename
from certificate_generator import CertificateGenerator
from pdf_uploader import PDFUploader
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

# Allowed file extensions for uploads
ALLOWED_FONT_EXTENSIONS = {"ttf", "otf"}
ALLOWED_TEMPLATE_EXTENSIONS = {"png", "jpg", "jpeg"}

generation_lock = Lock()
is_generating = False
cancel_requested = False


def get_csv_hash(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def read_csv_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if config.NAME_COLUMN not in fieldnames:
            raise ValueError(f"CSV must contain '{config.NAME_COLUMN}' column")
        rows = [row for row in reader if row.get(config.NAME_COLUMN, "").strip()]
    return rows, fieldnames


def read_generated_csv():
    """Read existing generated CSV and return processed names, results, and CSV hash"""
    if not os.path.exists(config.GENERATED_CSV):
        return set(), [], None

    with open(config.GENERATED_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        results = []
        for row in reader:
            # Clean up any None keys that might exist from mismatched columns
            cleaned_row = {k: v for k, v in row.items() if k is not None}
            # Ensure error field exists
            if "error" not in cleaned_row:
                cleaned_row["error"] = ""
            results.append(cleaned_row)

        processed = {r[config.NAME_COLUMN] for r in results if config.NAME_COLUMN in r}
        csv_hash = results[0].get("_csv_hash") if results else None
    return processed, results, csv_hash


def append_to_generated_csv(result, fieldnames, csv_hash):
    """Append a single result to generated CSV (creates file if doesn't exist)"""
    file_exists = os.path.exists(config.GENERATED_CSV)
    output_fields = ["_csv_hash"] + list(
        dict.fromkeys(list(fieldnames) + ["url", "status", "error"])
    )

    with open(config.GENERATED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow({**result, "_csv_hash": csv_hash})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    try:
        if "file" not in request.files or not request.files["file"].filename:
            return jsonify({"success": False, "error": "No file selected"}), 400

        file = request.files["file"]
        if not config.allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        filepath = os.path.join(config.UPLOAD_DIR, "current.csv")
        file.save(filepath)

        try:
            rows, fieldnames = read_csv_data(filepath)
        except ValueError as e:
            os.remove(filepath)
            return jsonify({"success": False, "error": str(e)}), 400

        csv_hash = get_csv_hash(filepath)
        processed, _, existing_hash = read_generated_csv()
        is_new_csv = existing_hash and existing_hash != csv_hash

        return jsonify(
            {
                "success": True,
                "message": f"CSV uploaded with {len(rows)} entries",
                "total_entries": len(rows),
                "is_new_csv": is_new_csv,
                "previous_progress": len(processed) if is_new_csv else 0,
            }
        )
    except Exception as e:
        logger.exception("Error uploading CSV")
        return jsonify({"success": False, "error": "An internal error occurred while uploading the CSV"}), 500


@app.route("/check-progress")
def check_progress():
    global is_generating
    processed, results, csv_hash = read_generated_csv()
    has_progress = len(processed) > 0

    current_csv_path = os.path.join(config.UPLOAD_DIR, "current.csv")
    has_csv = os.path.exists(current_csv_path)
    csv_matches = False
    is_complete = False

    if has_csv and csv_hash:
        current_hash = get_csv_hash(current_csv_path)
        csv_matches = current_hash == csv_hash

        if csv_matches:
            try:
                rows, _ = read_csv_data(current_csv_path)
                is_complete = len(processed) == len(rows)
            except:
                pass

    return jsonify(
        {
            "has_progress": has_progress,
            "processed_count": len(processed),
            "results": results,
            "has_csv": has_csv,
            "csv_matches": csv_matches,
            "is_complete": is_complete,
            "is_generating": is_generating,
        }
    )


@app.route("/reset-progress", methods=["POST"])
def reset_progress():
    try:
        if os.path.exists(config.GENERATED_CSV):
            os.remove(config.GENERATED_CSV)
        return jsonify({"success": True, "message": "Progress reset"})
    except Exception as e:
        logger.exception("Error resetting progress")
        return jsonify({"success": False, "error": "An internal error occurred while resetting progress"}), 500


@app.route("/cancel-generation", methods=["POST"])
def cancel_generation():
    global cancel_requested
    cancel_requested = True
    return jsonify({"success": True, "message": "Cancellation requested"})


@app.route("/generate", methods=["POST"])
def generate_certificates():
    global is_generating, cancel_requested

    if not generation_lock.acquire(blocking=False):
        return jsonify({
            "success": False,
            "error": "Generation already in progress. Please wait for it to complete."
        }), 409

    try:
        is_generating = True
        cancel_requested = False
        csv_path = os.path.join(config.UPLOAD_DIR, "current.csv")
        if not os.path.exists(csv_path):
            return jsonify({"success": False, "error": "No CSV uploaded"}), 400

        rows, fieldnames = read_csv_data(csv_path)
        csv_hash = get_csv_hash(csv_path)
        processed_names, all_results, existing_hash = read_generated_csv()

        if existing_hash and existing_hash != csv_hash:
            return (
                jsonify({"success": False, "error": "CSV changed, reset progress"}),
                400,
            )

        generator = CertificateGenerator()
        uploader = (
            PDFUploader(
                service=config.UPLOAD_SERVICE,
                cloudinary_config=config.get_cloudinary_config(),
                cloudinary_folder=config.CLOUDINARY_FOLDER,
            )
            if config.UPLOAD_SERVICE == "cloudinary"
            else PDFUploader(service=config.UPLOAD_SERVICE)
        )

        new_results = []
        cancelled = False

        for row in rows:
            if cancel_requested:
                cancelled = True
                print("⚠️  Generation cancelled by user")
                break

            name = row[config.NAME_COLUMN].strip()
            if name in processed_names:
                continue

            try:
                pdf_path = generator.generate_certificate(name)
                url = uploader.upload(pdf_path, name)
                result = {**row, "url": url, "status": "success"}
                print(f"✓ {name} -> {url}")
            except Exception as e:
                result = {**row, "url": "", "status": "error", "error": str(e)}
                print(f"✗ {name}: {e}")

            try:
                append_to_generated_csv(result, fieldnames, csv_hash)
                all_results.append(result)
                new_results.append(result)
                processed_names.add(name)
            except Exception as e:
                print(f"✗ Failed to save progress for {name}: {e}")
                pass

        return jsonify(
            {
                "success": True,
                "message": f"Generated {len(new_results)} certificates" + (" (cancelled)" if cancelled else ""),
                "results": all_results,
                "new_results": new_results,
                "completed": len(processed_names) == len(rows),
                "cancelled": cancelled,
            }
        )
    except Exception as e:
        logger.exception("Error generating certificates")
        return jsonify({"success": False, "error": "An internal error occurred while generating certificates"}), 500
    finally:
        is_generating = False
        cancel_requested = False
        generation_lock.release()


@app.route("/download-csv")
def download_csv():
    if not os.path.exists(config.GENERATED_CSV):
        return jsonify({"error": "CSV not found"}), 404
    return send_file(
        config.GENERATED_CSV, as_attachment=True, download_name="certificates.csv"
    )


# ============ Settings API Endpoints ============

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current visual settings"""
    settings = config.load_settings()
    return jsonify(settings)


@app.route("/api/settings", methods=["POST"])
def save_settings():
    """Save visual settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Validate required fields
        current_settings = config.load_settings()
        updated_settings = {**current_settings, **data}

        # Validate template exists
        template_path = os.path.join(config.TEMPLATES_DIR, updated_settings["template"])
        if not os.path.exists(template_path):
            return jsonify({"success": False, "error": f"Template not found: {updated_settings['template']}"}), 400

        # Validate font exists
        if not os.path.exists(updated_settings["font_path"]):
            return jsonify({"success": False, "error": f"Font not found: {updated_settings['font_path']}"}), 400

        config.save_settings(updated_settings)
        return jsonify({"success": True, "settings": updated_settings})
    except Exception as e:
        logger.exception("Error saving settings")
        return jsonify({"success": False, "error": "An internal error occurred while saving settings"}), 500


@app.route("/api/templates", methods=["GET"])
def list_templates():
    """List available certificate templates"""
    templates = []
    if os.path.exists(config.TEMPLATES_DIR):
        for f in os.listdir(config.TEMPLATES_DIR):
            ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
            if ext in ALLOWED_TEMPLATE_EXTENSIONS:
                templates.append({
                    "name": f.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
                    "filename": f
                })
    return jsonify({"templates": templates})


@app.route("/api/fonts", methods=["GET"])
def list_fonts():
    """List available fonts"""
    fonts = []
    if os.path.exists(config.FONTS_DIR):
        for f in os.listdir(config.FONTS_DIR):
            ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
            if ext in ALLOWED_FONT_EXTENSIONS:
                fonts.append({
                    "name": f.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
                    "path": os.path.join(config.FONTS_DIR, f)
                })
    return jsonify({"fonts": fonts})


@app.route("/api/upload-template", methods=["POST"])
def upload_template():
    """Upload a new certificate template"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_TEMPLATE_EXTENSIONS:
            return jsonify({"success": False, "error": f"Invalid file type. Allowed: {', '.join(ALLOWED_TEMPLATE_EXTENSIONS)}"}), 400

        filename = secure_filename(file.filename)
        os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
        filepath = os.path.join(config.TEMPLATES_DIR, filename)
        file.save(filepath)

        return jsonify({
            "success": True,
            "filename": filename,
            "message": f"Template '{filename}' uploaded successfully"
        })
    except Exception as e:
        logger.exception("Error uploading template")
        return jsonify({"success": False, "error": "An internal error occurred while uploading the template"}), 500


@app.route("/api/upload-font", methods=["POST"])
def upload_font():
    """Upload a new font file"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_FONT_EXTENSIONS:
            return jsonify({"success": False, "error": f"Invalid file type. Allowed: {', '.join(ALLOWED_FONT_EXTENSIONS)}"}), 400

        filename = secure_filename(file.filename)
        os.makedirs(config.FONTS_DIR, exist_ok=True)
        filepath = os.path.join(config.FONTS_DIR, filename)
        file.save(filepath)

        return jsonify({
            "success": True,
            "path": filepath,
            "filename": filename,
            "message": f"Font '{filename}' uploaded successfully"
        })
    except Exception as e:
        logger.exception("Error uploading font")
        return jsonify({"success": False, "error": "An internal error occurred while uploading the font"}), 500


@app.route("/api/preview", methods=["POST"])
def generate_preview():
    """Generate a preview image with the given settings"""
    try:
        data = request.get_json() or {}
        name = data.pop("name", "Sample Name")

        # Merge with current settings
        current_settings = config.load_settings()
        preview_settings = {**current_settings, **data}

        generator = CertificateGenerator(settings=preview_settings)
        preview = generator.generate_preview(name=name, settings=preview_settings)

        return jsonify({"success": True, "preview": preview})
    except FileNotFoundError as e:
        logger.exception("File not found while generating preview")
        return jsonify({"success": False, "error": "Required file not found for preview generation"}), 404
    except Exception as e:
        logger.exception("Error generating preview")
        return jsonify({"success": False, "error": "An internal error occurred while generating the preview"}), 500


if __name__ == "__main__":
    try:
        config.validate_setup()
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not config.DEBUG_MODE:
            print("✅ Configuration validated successfully")
            print(f"📁 Certificate template: {config.CERTIFICATE_TEMPLATE}")
            print(f"☁️  Upload service: {config.UPLOAD_SERVICE}")
            print(f"🚀 Starting server on {config.HOST}:{config.PORT}")
        app.run(debug=config.DEBUG_MODE, port=config.PORT, host=config.HOST)
    except ValueError as e:
        print(str(e))
        print("\n💡 Tip: Check the README.md for setup instructions")
        exit(1)
