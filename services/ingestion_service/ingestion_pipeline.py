import os
import tempfile

from sqlalchemy.orm import Session
from shared.database.session import SessionLocal
from shared.models.document import Document
from services.ingestion_service.parser_service import extract_text_from_document
from services.privacy_service.pii_redactor import redact_text
from services.storage_service.storage_service import StorageService
from services.risk_service.risk_detector import run_risk_detection_pipeline
from workers.tasks.extraction_tasks import extract_document_facts


def _store_document_chunks(document_id: str, text: str):
    from services.extraction_service.vector_service import store_document_chunks

    store_document_chunks(document_id, text)


def run_ingestion_pipeline(document_id: str):
    db: Session = SessionLocal()
    document = None
    downloaded_path = None
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        document.document_status = "PROCESSING"
        db.commit()

        storage_service = StorageService()
        suffix = os.path.splitext(document.file_name or "")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            downloaded_path = temp_file.name

        storage_service.download_file(document.storage_path, downloaded_path)
        extracted_text = extract_text_from_document(downloaded_path)
        print("Extracted Text Length:", len(extracted_text))
        redacted_text, redactions = redact_text(extracted_text)
        print("PII Redactions Applied:", len(redactions))
        _store_document_chunks(str(document.id), redacted_text)
        try:
            run_risk_detection_pipeline(str(document.id), redacted_text)
        except Exception as risk_error:
            print(f"Risk detection failed for document {document.id}: {risk_error}")

        document.document_status = "EXTRACTED"
        db.commit()
        db.refresh(document)
        
    except Exception:
        db.rollback()
        if document is not None:
            try:
                document.document_status = "FAILED"
                db.commit()
            except Exception:
                db.rollback()
        raise

    finally:
        if downloaded_path and os.path.exists(downloaded_path):
            os.remove(downloaded_path)
        db.close()
