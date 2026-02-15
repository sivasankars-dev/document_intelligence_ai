import re
from collections import defaultdict

from shared.config.settings import settings

EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:"
    r"\+?\d{1,3}[-.\s]\d{3}[-.\s]\d{3}[-.\s]\d{4}"
    r"|"
    r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}"
    r")(?!\w)"
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def _luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def redact_text(text: str) -> tuple[str, list[dict]]:
    if not settings.PII_REDACTION_ENABLED:
        return text, []

    counters = defaultdict(int)
    token_cache: dict[tuple[str, str], str] = {}
    redactions: list[dict] = []

    def _tokenize(pii_type: str, raw_value: str) -> str:
        key = (pii_type, raw_value)
        if key not in token_cache:
            counters[pii_type] += 1
            token = f"[PII_{pii_type}_{counters[pii_type]}]"
            token_cache[key] = token
            redactions.append(
                {
                    "placeholder": token,
                    "pii_type": pii_type,
                    "value": raw_value,
                }
            )
        return token_cache[key]

    redacted = text
    redacted = EMAIL_PATTERN.sub(lambda m: _tokenize("EMAIL", m.group(0)), redacted)
    redacted = SSN_PATTERN.sub(lambda m: _tokenize("SSN", m.group(0)), redacted)
    redacted = PHONE_PATTERN.sub(lambda m: _tokenize("PHONE", m.group(0)), redacted)

    def _card_replacer(match: re.Match[str]) -> str:
        raw = match.group(0)
        digits_only = re.sub(r"\D", "", raw)
        if _luhn_valid(digits_only):
            return _tokenize("CARD", raw)
        return raw

    redacted = CARD_PATTERN.sub(_card_replacer, redacted)
    return redacted, redactions
