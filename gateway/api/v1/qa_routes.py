from fastapi import APIRouter, Depends
from pydantic import BaseModel

from gateway.dependencies.auth import get_current_user

try:
    from services.qa_service.qa_pipeline import run_qa_pipeline
except ModuleNotFoundError:
    def run_qa_pipeline(question: str, document_id: str):
        raise RuntimeError("QA pipeline dependencies are not installed.")

router = APIRouter()

class QARequest(BaseModel):
    question: str
    document_id: str

@router.post("/ask")
def ask_question(
    payload: QARequest,
    current_user = Depends(get_current_user)
):
    answer = run_qa_pipeline(
        payload.question,
        payload.document_id
    )

    return {"answer": answer}
