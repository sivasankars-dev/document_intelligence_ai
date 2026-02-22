import re
import uuid
from typing import Iterable

from shared.database.session import SessionLocal
from shared.models.risk import Risk
from services.risk_service.risk_repository import RiskRepository


RISK_RULES = [
    {
        "name": "auto_renewal",
        "severity": "MEDIUM",
        "confidence": 0.78,
        "patterns": [r"\bauto[-\s]?renew", r"\bautomatic(?:ally)? renew"],
        "description": "Auto-renewal clause detected. Review cancellation timeline.",
    },
    {
        "name": "termination_fee",
        "severity": "HIGH",
        "confidence": 0.86,
        "patterns": [r"\btermination fee", r"\bpenalt(?:y|ies)\b", r"\bearly exit fee"],
        "description": "Termination penalty clause detected.",
    },
    {
        "name": "broad_data_sharing",
        "severity": "HIGH",
        "confidence": 0.82,
        "patterns": [r"\bshare (?:your )?data with third parties", r"\bthird[-\s]?party data sharing"],
        "description": "Broad third-party data sharing clause detected.",
    },
    {
        "name": "indemnity",
        "severity": "HIGH",
        "confidence": 0.8,
        "patterns": [r"\bindemnif(?:y|ication)\b", r"\bhold harmless\b"],
        "description": "Indemnity obligation clause detected.",
    },
    {
        "name": "liability_limitation",
        "severity": "MEDIUM",
        "confidence": 0.74,
        "patterns": [r"\blimitation of liability\b", r"\bnot liable for\b"],
        "description": "Liability limitation clause detected.",
    },
]


def _extract_candidate_sentences(text: str) -> Iterable[str]:
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    return [sentence.strip() for sentence in sentences if sentence and sentence.strip()]


def detect_risks(text: str) -> list[dict]:
    sentences = _extract_candidate_sentences(text)
    findings = []
    seen = set()
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for rule in RISK_RULES:
            if any(re.search(pattern, sentence_lower, re.IGNORECASE) for pattern in rule["patterns"]):
                key = (rule["name"], sentence_lower[:120])
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    {
                        "description": f"{rule['description']} Source: {sentence[:260]}",
                        "severity": rule["severity"],
                        "confidence_score": rule["confidence"],
                        "detected_by": "rule_engine",
                    }
                )
    return findings


def persist_detected_risks(db, document_id: str, findings: list[dict]) -> list[Risk]:
    created = []
    for finding in findings:
        risk = Risk(
            id=uuid.uuid4(),
            document_id=document_id,
            description=finding["description"],
            severity=finding["severity"],
            confidence_score=finding.get("confidence_score"),
            detected_by=finding.get("detected_by", "rule_engine"),
        )
        created.append(RiskRepository.create(db, risk))
    return created


def run_risk_detection_pipeline(document_id: str, text: str):
    db = SessionLocal()
    try:
        findings = detect_risks(text)
        if not findings:
            return []
        return persist_detected_risks(db, document_id, findings)
    finally:
        db.close()
