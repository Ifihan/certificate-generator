import os
import csv
import hashlib
from threading import Lock
from flask import Flask, render_template, jsonify, send_file, request
from certificate_generator import CertificateGenerator
from pdf_uploader import PDFUploader
import config

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

generation_lock = Lock()
is_generating = False


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
        return jsonify({"success": False, "error": str(e)}), 500


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
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate_certificates():
    global is_generating

    if not generation_lock.acquire(blocking=False):
        return jsonify({
            "success": False,
            "error": "Generation already in progress. Please wait for it to complete."
        }), 409

    try:
        is_generating = True
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

        for row in rows:
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
                "message": f"Generated {len(new_results)} certificates",
                "results": all_results,
                "new_results": new_results,
                "completed": len(processed_names) == len(rows),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        is_generating = False
        generation_lock.release()


@app.route("/download-csv")
def download_csv():
    if not os.path.exists(config.GENERATED_CSV):
        return jsonify({"error": "CSV not found"}), 404
    return send_file(
        config.GENERATED_CSV, as_attachment=True, download_name="certificates.csv"
    )


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
