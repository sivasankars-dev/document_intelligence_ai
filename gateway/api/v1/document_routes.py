from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from shared.database.session import get_db
from shared.schemas.document_schema import DocumentResponse
from services.document_service.document_service import DocumentService
from gateway.dependencies.auth import get_current_user

router = APIRouter()

def get_document_service() -> DocumentService:
    return DocumentService()


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    document = document_service.upload_document(
        db=db,
        file=file,
        user_id=user["user_id"]
    )

    return document
