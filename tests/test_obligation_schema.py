from datetime import datetime
from services.obligation_service.schemas import (
    ObligationCandidate,
    ObligationStructured,
)

def test_obligation_candidate():
    candidate = ObligationCandidate(
        sentence="Premium must be paid before 10 March 2026"
    )

    assert candidate.sentence is not None


def test_obligation_structured():
    obligation = ObligationStructured(
        title="Premium Payment",
        due_date=datetime(2026, 3, 10),
        confidence_score=0.9,
    )

    assert obligation.title == "Premium Payment"
    assert obligation.confidence_score <= 1.0
