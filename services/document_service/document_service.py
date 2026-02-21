import os

from sqlalchemy.orm import Session
from shared.models.document import Document
from shared.models.document_version import DocumentVersion
from services.storage_service.storage_service import StorageService
from shared.config.settings import settings

try:
    from workers.tasks.ingestion_tasks import ingest_document_task
except ModuleNotFoundError:
    ingest_document_task = None

class DocumentService:
    def __init__(self):
        self.storage = StorageService()

    def _validate_upload(self, file):
        allowed_types = {
            value.strip().lower()
            for value in settings.ALLOWED_UPLOAD_CONTENT_TYPES.split(",")
            if value.strip()
        }
        allowed_extensions = {
            value.strip().lower()
            for value in settings.ALLOWED_UPLOAD_EXTENSIONS.split(",")
            if value.strip()
        }

        content_type = (file.content_type or "").lower()
        extension = os.path.splitext(file.filename or "")[1].lower()

        if content_type not in allowed_types:
            raise ValueError(f"Unsupported content type: {file.content_type}")
        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported file extension: {extension or 'none'}")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        current_pos = file.file.tell()
        file.file.seek(0, os.SEEK_END)
        size_bytes = file.file.tell()
        file.file.seek(current_pos, os.SEEK_SET)
        if size_bytes > max_bytes:
            raise ValueError(
                f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB"
            )

    def upload_document(self,db: Session,file,user_id):
        self._validate_upload(file)
        storage_path = self.storage.upload_file(file.file,file.filename)

        document = Document(
            user_id=user_id,
            file_name=file.filename,
            file_type=file.content_type,
            storage_path=storage_path
        )

        db.add(document)
        db.flush()

        # Create Version 1
        version = DocumentVersion(
            document_id=document.id,
            version_number=1
        )

        db.add(version)
        db.commit()
        db.refresh(document)
        
        if ingest_document_task is not None:
            ingest_document_task.delay(str(document.id))

        return document
