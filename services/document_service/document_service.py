from sqlalchemy.orm import Session
from shared.models.document import Document
from shared.models.document_version import DocumentVersion
from services.storage_service.storage_service import StorageService


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
        db.commit()
        db.refresh(document)

        # Create Version 1
        version = DocumentVersion(
            document_id=document.id,
            version_number=1
        )

        db.add(version)
        db.commit()

        return document
