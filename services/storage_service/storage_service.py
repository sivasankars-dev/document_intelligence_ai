import uuid
import json
from pathlib import Path

try:
    from google.cloud import storage
    from google.oauth2 import service_account
except (ModuleNotFoundError, ImportError):
    storage = None
    service_account = None

from shared.config.settings import settings


class StorageService:
    def __init__(self):
        if storage is None:
            raise RuntimeError("google-cloud-storage package is required for StorageService")
        if service_account is None:
            raise RuntimeError("google-auth package is required for StorageService")

        credentials = None
        if settings.GCS_CREDENTIALS_JSON:
            info = json.loads(settings.GCS_CREDENTIALS_JSON)
            credentials = service_account.Credentials.from_service_account_info(info)
        elif settings.GCS_CREDENTIALS_FILE:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GCS_CREDENTIALS_FILE
            )

        # If no explicit key is provided, rely on ADC (e.g., Compute Engine service account).
        if credentials is not None:
            self.client = storage.Client(project=settings.GCP_PROJECT_ID, credentials=credentials)
        elif settings.GCP_PROJECT_ID:
            self.client = storage.Client(project=settings.GCP_PROJECT_ID)
        else:
            self.client = storage.Client()
        self.bucket_name = settings.GCS_BUCKET
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(self, file_obj, filename):
        object_name = f"{uuid.uuid4()}_{filename}"
        blob = self.bucket.blob(object_name)
        file_obj.seek(0)
        blob.upload_from_file(file_obj, rewind=True)

        return object_name

    def download_file(self, object_name: str, destination_path: str):
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        blob = self.bucket.blob(object_name)
        blob.download_to_filename(destination_path)
        return destination_path
