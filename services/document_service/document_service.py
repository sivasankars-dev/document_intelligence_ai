from sqlalchemy.orm import Session
from shared.models.document import Document
from shared.models.document_version import DocumentVersion
from services.storage_service.storage_service import StorageService

try:
    from workers.tasks.ingestion_tasks import ingest_document_task
except ModuleNotFoundError:
    ingest_document_task = None

class DocumentService:
    def __init__(self):
        self.storage = StorageService()

    def upload_document(self,db: Session,file,user_id):
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
