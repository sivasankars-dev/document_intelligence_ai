import pytest

import services.obligation_service.obligation_detector as obligation_detector
from services.obligation_service.obligation_detector import detect_obligations
from services.obligation_service.schemas import ObligationStructured


@pytest.mark.asyncio
async def test_detect_obligations(monkeypatch):
    text = """
    Premium must be paid before 10 March 2026.
    Policy shall be renewed within 30 days.
    """

    async def fake_validate_obligation(sentence: str):
        return ObligationStructured(
            title=sentence[:80],
            due_date=None,
            confidence_score=0.91,
        )

    monkeypatch.setattr(
        obligation_detector,
        "_resolve_validator",
        lambda: fake_validate_obligation,
    )

    results = await detect_obligations(
        document_id="test-doc-id",
        text=text,
    )

    assert len(results) == 2
    assert all(item.document_id == "test-doc-id" for item in results)
    assert all(item.confidence_score == 0.91 for item in results)
    assert results[0].title == "Premium must be paid before 10 March 2026"
    assert results[0].due_date is None
    assert results[1].title == "Policy shall be renewed within 30 days"
    assert results[1].due_date is None


@pytest.mark.asyncio
async def test_detect_obligations_returns_empty_when_no_candidates():
    results = await detect_obligations(
        document_id="test-doc-id",
        text="This is an informational paragraph describing product background only.",
    )

    assert results == []
