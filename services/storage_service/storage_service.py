import uuid
from pathlib import Path

try:
    from minio import Minio
except ModuleNotFoundError:
    Minio = None

from shared.config.settings import settings


class StorageService:
    def __init__(self):
        if Minio is None:
            raise RuntimeError("minio package is required for StorageService")
        
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_obj, filename):
        object_name = f"{uuid.uuid4()}_{filename}"
        self.client.put_object(
            self.bucket,
            object_name,
            file_obj,
            length=-1,
            part_size=10 * 1024 * 1024
        )

        return object_name

    def download_file(self, object_name: str, destination_path: str):
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        self.client.fget_object(self.bucket, object_name, destination_path)
        return destination_path
