import requests
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

class PDFUploader:
    """Upload PDFs to file hosting services and get shareable links"""

    def __init__(self, service='fileio', cloudinary_config=None):
        """Initialize the uploader"""
        self.service = service
        self.cloudinary_config = cloudinary_config

        if service == 'cloudinary':
            if not cloudinary_config:
                raise ValueError("cloudinary_config is required when using cloudinary service")
            cloudinary.config(
                cloud_name=cloudinary_config.get('cloud_name'),
                api_key=cloudinary_config.get('api_key'),
                api_secret=cloudinary_config.get('api_secret'),
                secure=True
            )

    def upload(self, file_path, name):
        """Upload a file and return its public URL"""
        if self.service == 'cloudinary':
            return self._upload_cloudinary(file_path, name)
        elif self.service == 'fileio':
            return self._upload_fileio(file_path)
        elif self.service == 'tmpfiles':
            return self._upload_tmpfiles(file_path)
        elif self.service == 'catbox':
            return self._upload_catbox(file_path)
        else:
            raise ValueError(f"Unknown service: {self.service}")

    def _upload_cloudinary(self, file_path, name):
        """Upload to Cloudinary"""
        try:
            sanitized_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            sanitized_name = sanitized_name.replace(' ', '_')
            public_id = f"icair_certificates/{sanitized_name}"

            response = cloudinary.uploader.upload(
                file_path,
                resource_type="raw",
                public_id=public_id,
                overwrite=True,
                folder="icair_certificates"
            )

            secure_url = response.get('secure_url')
            if secure_url:
                return secure_url
            else:
                raise Exception(f"Upload succeeded but no URL returned: {response}")

        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")

    def _upload_fileio(self, file_path):
        """Upload to file.io"""
        url = "https://file.io/"

        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'expires': '1y'}

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()

            result = response.json()
            if result.get('success'):
                return result['link']
            else:
                raise Exception(f"Upload failed: {result.get('message', 'Unknown error')}")

    def _upload_tmpfiles(self, file_path):
        """Upload to tmpfiles.org"""
        url = "https://tmpfiles.org/api/v1/upload"

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
            response.raise_for_status()

            result = response.json()
            if result.get('status') == 'success':
                original_url = result['data']['url']
                download_url = original_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                return download_url
            else:
                raise Exception(f"Upload failed: {result.get('message', 'Unknown error')}")

    def _upload_catbox(self, file_path):
        """Upload to catbox.moe"""
        url = "https://catbox.moe/user/api.php"

        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()

            file_url = response.text.strip()
            if file_url.startswith('http'):
                return file_url
            else:
                raise Exception(f"Upload failed: {file_url}")


class LocalFileStore:
    """For testing: stores files locally and returns file:// URLs"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def upload(self, file_path, name):
        """Return a file:// URL to the local file"""
        abs_path = os.path.abspath(file_path)
        return f"file://{abs_path}"
