import hashlib
import re
from openai import OpenAI
from shared.cache import get_cache_service
from shared.config.settings import settings

from services.qa_service.retriever_service import retrieve_document_chunks
from services.qa_service.prompt_service import build_reasoning_qa_prompt
from services.privacy_service.pii_redactor import redact_text

client = OpenAI(api_key=settings.OPENAI_API_KEY)
QA_RESPONSE_CACHE_VERSION = "v1"


def _is_document_advice_question(question: str) -> bool:
    q = question.lower()
    keywords = [
        "document",
        "resume",
        "candidate",
        "policy",
        "insurance",
        "agreement",
        "contract",
        "hire",
        "fit",
        "good to me",
        "recommend",
        "mutual fund",
        "index fund",
    ]
    return any(k in q for k in keywords)


def _is_rejection_answer(answer: str) -> bool:
    text = (answer or "").strip().lower()
    return (
        "please ask about document" in text
        or "ask about document" in text
        or text == "please ask about the document."
    )


def _normalize_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def _classify_query(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["compare", "vs", "versus", "better than"]):
        return "comparison"
    if any(k in q for k in ["why", "problem", "risk", "issue", "drawback"]):
        return "analysis"
    if any(k in q for k in ["should i", "recommend", "advice", "suggest"]):
        return "recommendation"
    if any(k in q for k in ["when", "date", "deadline", "due", "expiry"]):
        return "timeline"
    return "fact"


def _build_query_variants(question: str, query_type: str) -> list[str]:
    variants = [question]
    if query_type == "analysis":
        variants.extend(
            [
                f"key risks and problems in this document: {question}",
                f"critical clauses and red flags: {question}",
            ]
        )
    elif query_type == "comparison":
        variants.extend(
            [
                f"comparison points and trade-offs in this document: {question}",
                f"benefits, limitations, and conditions: {question}",
            ]
        )
    elif query_type == "recommendation":
        variants.extend(
            [
                f"decision factors and suitability from this document: {question}",
                f"pros, cons, and risk profile: {question}",
            ]
        )
    elif query_type == "timeline":
        variants.extend(
            [
                f"due dates, deadlines, and expiry terms: {question}",
                f"timeline obligations and renewal events: {question}",
            ]
        )
    else:
        variants.append(f"important facts from this document: {question}")

    unique = []
    seen = set()
    for variant in variants:
        key = variant.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(variant)
    return unique[:4]


def _build_evidence(question: str, document_id: str, query_type: str) -> list[dict]:
    variants = _build_query_variants(question, query_type)
    q_tokens = _normalize_tokens(question)
    by_chunk: dict[str, dict] = {}

    for variant_index, variant in enumerate(variants):
        chunks = retrieve_document_chunks(variant, document_id)
        for rank, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_tokens = _normalize_tokens(chunk)
            overlap = len(q_tokens & chunk_tokens) / max(1, len(q_tokens))
            rank_score = 1.0 / (rank + 1)
            variant_boost = 1.0 - (0.15 * variant_index)
            score = (0.65 * rank_score + 0.35 * overlap) * max(0.55, variant_boost)
            existing = by_chunk.get(chunk)
            if existing is None:
                by_chunk[chunk] = {
                    "text": chunk,
                    "score": score,
                    "support_queries": [variant],
                }
            else:
                existing["score"] = max(existing["score"], score)
                if variant not in existing["support_queries"]:
                    existing["support_queries"].append(variant)

    evidence = sorted(by_chunk.values(), key=lambda x: x["score"], reverse=True)
    return evidence[:8]


def _infer_missing_info(question: str, query_type: str, evidence_chunks: list[str]) -> list[str]:
    combined = " ".join(evidence_chunks).lower()
    hints: list[str] = []
    if query_type in {"comparison", "recommendation"}:
        for term in ["premium", "cost", "returns", "tenure", "coverage", "penalty"]:
            if term in question.lower() and term not in combined:
                hints.append(term)
    if query_type == "timeline":
        if not any(term in combined for term in ["due", "date", "deadline", "expiry"]):
            hints.append("specific dates or deadlines")
    if query_type == "analysis":
        if "risk" in question.lower() and "risk" not in combined:
            hints.append("explicit risk clauses")
    return hints[:5]


def _confidence_from_evidence(evidence: list[dict]) -> tuple[float, str]:
    if not evidence:
        return 0.0, "low"
    top = evidence[:3]
    avg_score = sum(item["score"] for item in top) / len(top)
    support_factor = min(1.0, sum(len(item["support_queries"]) for item in top) / 6.0)
    confidence = min(0.99, 0.7 * avg_score + 0.3 * support_factor)
    band = "high" if confidence >= 0.72 else "medium" if confidence >= 0.45 else "low"
    return round(confidence, 2), band


def _qa_response_cache_key(question: str, document_id: str) -> str:
    q_hash = hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()
    return f"qa:response:{QA_RESPONSE_CACHE_VERSION}:{document_id}:{q_hash}"


def run_qa_pipeline_with_metadata(question: str, document_id: str) -> dict:
    cache = get_cache_service()
    cache_key = _qa_response_cache_key(question=question, document_id=document_id)
    cached_result = cache.get_json(cache_key)
    if isinstance(cached_result, dict) and cached_result.get("answer"):
        return cached_result

    query_type = _classify_query(question)
    evidence = _build_evidence(question, document_id, query_type)
    if not evidence:
        result = {
            "answer": "No relevant information found.",
            "query_type": query_type,
            "confidence": 0.0,
            "confidence_band": "low",
            "missing_information": ["No indexed chunks found for this document."],
            "evidence_count": 0,
            "citations": [],
        }
        cache.set_json(cache_key, result, ttl_seconds=settings.QA_RESPONSE_CACHE_TTL_SECONDS)
        return result

    safe_chunks = [redact_text(item["text"])[0] for item in evidence]
    missing_info = _infer_missing_info(question, query_type, safe_chunks)
    prompt = build_reasoning_qa_prompt(question, query_type, safe_chunks, missing_info)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document QA assistant. "
                    "Only reply 'Please ask about document.' for truly unrelated questions. "
                    "If the user asks for advice/evaluation about the provided document, do not reject."
                ),
            },
            {"role": "user", "content": prompt},
        ]
    )

    answer = response.choices[0].message.content or ""
    if _is_rejection_answer(answer) and _is_document_advice_question(question):
        answer = (
            "Your question is related to this document. Based on retrieved context, "
            "I can provide guidance, but some details needed for a strong recommendation "
            "may be missing. Ask a focused follow-up like policy type, premium, tenure, "
            "returns, risk profile, and goals to get a better recommendation."
        )

    confidence, confidence_band = _confidence_from_evidence(evidence)
    citations = [
        {
            "evidence_id": f"EVIDENCE_{idx + 1}",
            "relevance_score": round(item["score"], 2),
            "matched_queries": item["support_queries"][:2],
            "snippet": redact_text(item["text"])[0][:220],
        }
        for idx, item in enumerate(evidence[:5])
    ]

    result = {
        "answer": answer,
        "query_type": query_type,
        "confidence": confidence,
        "confidence_band": confidence_band,
        "missing_information": missing_info,
        "evidence_count": len(evidence),
        "citations": citations,
    }
    cache.set_json(cache_key, result, ttl_seconds=settings.QA_RESPONSE_CACHE_TTL_SECONDS)
    return result


def run_qa_pipeline(question: str, document_id: str):
    result = run_qa_pipeline_with_metadata(question, document_id)
    return result["answer"]
