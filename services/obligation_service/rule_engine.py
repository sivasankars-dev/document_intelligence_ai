import re
from typing import List
from services.obligation_service.schemas import ObligationCandidate


# ---------------------------
# Obligation Keywords
# ---------------------------
OBLIGATION_KEYWORDS = [
    "must",
    "shall",
    "required",
    "due",
    "deadline",
    "renew",
    "expiry",
    "expires",
    "payment",
]


# ---------------------------
# Date Patterns
# ---------------------------
DATE_PATTERNS = [
    r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    r"\bwithin\s+\d+\s+days\b",
]


def _contains_keyword(sentence: str) -> bool:
    sentence_lower = sentence.lower()
    return any(keyword in sentence_lower for keyword in OBLIGATION_KEYWORDS)


def _contains_date(sentence: str) -> bool:
    return any(re.search(pattern, sentence, re.IGNORECASE) for pattern in DATE_PATTERNS)


def extract_candidates(text: str) -> List[ObligationCandidate]:
    """ Extract obligation candidate sentences from document text """

    if not text:
        return []

    # Simple sentence splitting
    sentences = re.split(r"[.\n]", text)

    candidates = []

    for sentence in sentences:
        cleaned = sentence.strip()

        if not cleaned:
            continue

        if _contains_keyword(cleaned) or _contains_date(cleaned):
            candidates.append(ObligationCandidate(sentence=cleaned))

    return candidates
