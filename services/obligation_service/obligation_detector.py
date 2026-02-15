from typing import List
from services.obligation_service.rule_engine import extract_candidates
from services.obligation_service.schemas import ObligationCreate
from shared.models.obligation import Obligation
from services.obligation_service.obligation_repository import ObligationRepository
import uuid


def _resolve_validator():
    try:
        from services.obligation_service.llm_validator import validate_obligation
        return validate_obligation
    except ModuleNotFoundError:
        async def _fallback_validator(_sentence: str):
            return None

        return _fallback_validator


async def detect_obligations(
    document_id: str,
    text: str,
) -> List[ObligationCreate]:
    """Main orchestration function for obligation detection"""
    validate_obligation = _resolve_validator()

    obligations: List[ObligationCreate] = []

    # -----------------------
    # Step 1: Extract Candidates
    # -----------------------
    candidates = extract_candidates(text)

    if not candidates:
        return obligations

    # -----------------------
    # Step 2: Validate via LLM
    # -----------------------
    for candidate in candidates:

        structured = await validate_obligation(candidate.sentence)

        if not structured:
            # fallback with low confidence
            obligations.append(
                ObligationCreate(
                    document_id=document_id,
                    title=candidate.sentence[:100],
                    due_date=None,
                    confidence_score=0.3,
                )
            )
            continue

        obligations.append(
            ObligationCreate(
                document_id=document_id,
                title=structured.title,
                due_date=structured.due_date,
                confidence_score=structured.confidence_score,
            )
        )

    return obligations

def persist_obligation(db, document, normalized_obligation):

    obligation = Obligation(
        id=uuid.uuid4(),
        document_id=document.id,
        user_id=document.user_id,
        title=normalized_obligation.title,
        description=normalized_obligation.description,
        category=normalized_obligation.category,
        due_date=normalized_obligation.due_date,
        recurrence=normalized_obligation.recurrence,
        priority=normalized_obligation.priority,
        risk_level=normalized_obligation.risk_level,
        confidence_score=normalized_obligation.confidence_score,
        detected_by=normalized_obligation.detected_by,
        source_text=normalized_obligation.source_text,
        status="PENDING"
    )

    ObligationRepository.create(db, obligation)
