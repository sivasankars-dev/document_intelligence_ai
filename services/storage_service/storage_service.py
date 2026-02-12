import uuid

try:
    from minio import Minio
except ModuleNotFoundError:
    Minio = None


class StorageService:
    def __init__(self):
        if Minio is None:
            raise RuntimeError("minio package is required for StorageService")
        
        self.client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        self.bucket = "documents"
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
