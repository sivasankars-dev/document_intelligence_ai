from services.obligation_service.rule_engine import extract_candidates


def test_extract_candidates_basic():
    text = """
    The premium must be paid before 10 March 2026.
    This document contains policy information.
    Policy shall be renewed within 30 days.
    """

    candidates = extract_candidates(text)

    assert len(candidates) >= 2
    assert "premium must be paid" in candidates[0].sentence.lower()
