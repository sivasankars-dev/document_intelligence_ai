import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from gateway.dependencies.auth import get_current_user
from shared.database.session import get_db
from shared.models.document import Document

try:
    from services.qa_service.qa_pipeline import (
        run_qa_pipeline,
        run_qa_pipeline_with_metadata,
    )
except ModuleNotFoundError:
    def run_qa_pipeline(question: str, document_id: str):
        raise RuntimeError("QA pipeline dependencies are not installed.")

    def run_qa_pipeline_with_metadata(question: str, document_id: str):
        raise RuntimeError("QA pipeline dependencies are not installed.")

router = APIRouter()

class QARequest(BaseModel):
    question: str
    document_id: str
    include_reasoning: bool = False


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

@router.post("/ask")
def ask_question(
    payload: QARequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_document_access(db, payload.document_id, current_user["user_id"])

    if payload.include_reasoning:
        return run_qa_pipeline_with_metadata(payload.question, payload.document_id)

    answer = run_qa_pipeline(
        payload.question,
        payload.document_id
    )

    return {"answer": answer}
