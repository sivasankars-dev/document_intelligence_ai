from services.privacy_service.pii_redactor import redact_text


def test_redact_text_replaces_common_pii(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        True,
    )
    text = (
        "Contact john.doe@example.com or +1 (415) 555-1234. "
        "SSN: 123-45-6789. Card: 4111 1111 1111 1111."
    )

    redacted_text, redactions = redact_text(text)

    assert "[PII_EMAIL_1]" in redacted_text
    assert "[PII_PHONE_1]" in redacted_text
    assert "[PII_SSN_1]" in redacted_text
    assert "[PII_CARD_1]" in redacted_text
    assert len(redactions) == 4


def test_redact_text_keeps_non_card_numbers(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        True,
    )
    text = "Order id 1234567890123 should remain unchanged."

    redacted_text, redactions = redact_text(text)

    assert "1234567890123" in redacted_text
    assert redactions == []


def test_redact_text_disabled_returns_original(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        False,
    )
    text = "Email me at a@b.com."

    redacted_text, redactions = redact_text(text)

    assert redacted_text == text
    assert redactions == []
