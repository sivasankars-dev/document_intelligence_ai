from services.risk_service.risk_detector import detect_risks


def test_detect_risks_finds_common_clauses():
    text = """
    This policy includes automatic renewal unless canceled.
    An early termination fee may apply.
    We may share your data with third parties.
    """

    findings = detect_risks(text)

    assert len(findings) >= 3
    severities = {item["severity"] for item in findings}
    assert "HIGH" in severities or "MEDIUM" in severities
