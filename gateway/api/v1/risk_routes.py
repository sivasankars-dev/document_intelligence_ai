import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gateway.dependencies.auth import get_current_user
from shared.database.session import get_db
from shared.models.document import Document
from shared.schemas.risk_schema import RiskResponse
from services.risk_service.risk_repository import RiskRepository

router = APIRouter()


def _ensure_document_access(db: Session, document_id: str, user_id):
    try:
        doc_uuid = uuid.UUID(str(document_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id format",
        ) from exc

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if str(document.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document",
        )
    return doc_uuid


@router.get("/document/{document_id}", response_model=list[RiskResponse])
def get_document_risks(
    document_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    doc_uuid = _ensure_document_access(db, document_id, user["user_id"])
    return RiskRepository.get_by_document(db, doc_uuid)
