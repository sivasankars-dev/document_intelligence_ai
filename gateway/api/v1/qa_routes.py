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
        run_qa_pipeline_for_documents,
        run_qa_pipeline_with_metadata,
        run_qa_pipeline_with_metadata_for_documents,
    )
except ModuleNotFoundError:
    def run_qa_pipeline(question: str, document_id: str):
        raise RuntimeError("QA pipeline dependencies are not installed.")

    def run_qa_pipeline_for_documents(question: str, document_ids: list[str], thread_id: str | None = None, user_id: str | None = None):
        raise RuntimeError("QA pipeline dependencies are not installed.")

    def run_qa_pipeline_with_metadata(question: str, document_id: str):
        raise RuntimeError("QA pipeline dependencies are not installed.")

    def run_qa_pipeline_with_metadata_for_documents(
        question: str,
        document_ids: list[str],
        thread_id: str | None = None,
        user_id: str | None = None,
    ):
        raise RuntimeError("QA pipeline dependencies are not installed.")

router = APIRouter()

class QARequest(BaseModel):
    question: str
    document_id: str | None = None
    document_ids: list[str] | None = None
    thread_id: str | None = None
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


def _resolve_document_ids(payload: QARequest) -> list[str]:
    candidates = []
    if payload.document_ids:
        candidates.extend(payload.document_ids)
    if payload.document_id:
        candidates.append(payload.document_id)

    deduped = []
    seen = set()
    for item in candidates:
        key = str(item).strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    if not deduped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one document_id must be provided",
        )
    return deduped

@router.post("/ask")
def ask_question(
    payload: QARequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document_ids = _resolve_document_ids(payload)
    for document_id in document_ids:
        _ensure_document_access(db, document_id, current_user["user_id"])

    if payload.include_reasoning:
        if len(document_ids) == 1 and payload.thread_id is None:
            return run_qa_pipeline_with_metadata(payload.question, document_ids[0])
        return run_qa_pipeline_with_metadata_for_documents(
            question=payload.question,
            document_ids=document_ids,
            thread_id=payload.thread_id,
            user_id=str(current_user["user_id"]),
        )

    if len(document_ids) == 1 and payload.thread_id is None:
        answer = run_qa_pipeline(payload.question, document_ids[0])
        return {"answer": answer}

    answer = run_qa_pipeline_for_documents(
        question=payload.question,
        document_ids=document_ids,
        thread_id=payload.thread_id,
        user_id=str(current_user["user_id"]),
    )
    return {"answer": answer}
