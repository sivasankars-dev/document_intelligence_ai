import hashlib
import re
from typing import Any

from openai import OpenAI

from shared.cache import get_cache_service
from shared.config.settings import settings
from services.privacy_service.pii_redactor import redact_text
from services.qa_service.prompt_service import build_reasoning_qa_prompt
from services.qa_service.retriever_service import retrieve_document_evidence

client = OpenAI(api_key=settings.OPENAI_API_KEY)
QA_RESPONSE_CACHE_VERSION = "v2"


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
    return any(keyword in q for keyword in keywords)


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
    if any(token in q for token in ["compare", "vs", "versus", "better than"]):
        return "comparison"
    if any(token in q for token in ["why", "problem", "risk", "issue", "drawback"]):
        return "analysis"
    if any(token in q for token in ["should i", "recommend", "advice", "suggest"]):
        return "recommendation"
    if any(token in q for token in ["when", "date", "deadline", "due", "expiry"]):
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
                f"comparison points and trade-offs in these documents: {question}",
                f"benefits, limitations, and conditions: {question}",
            ]
        )
    elif query_type == "recommendation":
        variants.extend(
            [
                f"decision factors and suitability from these documents: {question}",
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
        variants.append(f"important facts from these documents: {question}")

    deduped = []
    seen = set()
    for variant in variants:
        key = variant.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(variant)
    return deduped[:4]


def _build_evidence(question: str, document_ids: list[str], query_type: str) -> list[dict[str, Any]]:
    variants = _build_query_variants(question, query_type)
    question_tokens = _normalize_tokens(question)
    by_evidence_key: dict[str, dict[str, Any]] = {}

    for variant_index, variant in enumerate(variants):
        for doc_index, document_id in enumerate(document_ids):
            evidence_items = retrieve_document_evidence(variant, document_id, top_k=6)
            for rank, item in enumerate(evidence_items):
                text = item.get("text") or ""
                if not text:
                    continue
                text_tokens = _normalize_tokens(text)
                overlap = len(question_tokens & text_tokens) / max(1, len(question_tokens))
                rank_score = 1.0 / (rank + 1)
                variant_boost = 1.0 - (0.12 * variant_index)
                doc_boost = 1.0 - (0.03 * doc_index)
                distance = item.get("distance")
                distance_bonus = 1.0
                if isinstance(distance, (float, int)):
                    distance_bonus = max(0.65, 1.2 - float(distance))

                score = (0.6 * rank_score + 0.4 * overlap) * max(0.55, variant_boost) * max(0.85, doc_boost) * distance_bonus
                evidence_key = f"{item.get('document_id')}::{item.get('chunk_id') or hashlib.sha1(text.encode('utf-8')).hexdigest()}"

                existing = by_evidence_key.get(evidence_key)
                if existing is None:
                    by_evidence_key[evidence_key] = {
                        "text": text,
                        "document_id": item.get("document_id"),
                        "chunk_id": item.get("chunk_id"),
                        "chunk_index": item.get("chunk_index"),
                        "score": score,
                        "support_queries": [variant],
                    }
                else:
                    existing["score"] = max(existing["score"], score)
                    if variant not in existing["support_queries"]:
                        existing["support_queries"].append(variant)

    evidence = sorted(by_evidence_key.values(), key=lambda item: item["score"], reverse=True)
    return evidence[:10]


def _infer_missing_info(question: str, query_type: str, evidence_chunks: list[dict[str, Any]]) -> list[str]:
    combined = " ".join((item.get("text") or "").lower() for item in evidence_chunks)
    hints = []
    if query_type in {"comparison", "recommendation"}:
        for token in ["premium", "cost", "returns", "tenure", "coverage", "penalty"]:
            if token in question.lower() and token not in combined:
                hints.append(token)
    if query_type == "timeline":
        if not any(token in combined for token in ["due", "date", "deadline", "expiry"]):
            hints.append("specific dates or deadlines")
    if query_type == "analysis":
        if "risk" in question.lower() and "risk" not in combined:
            hints.append("explicit risk clauses")
    return hints[:5]


def _confidence_from_evidence(evidence: list[dict[str, Any]]) -> tuple[float, str]:
    if not evidence:
        return 0.0, "low"
    top = evidence[:3]
    avg_score = sum(item["score"] for item in top) / len(top)
    support_factor = min(1.0, sum(len(item["support_queries"]) for item in top) / 6.0)
    confidence = min(0.99, 0.7 * avg_score + 0.3 * support_factor)
    band = "high" if confidence >= 0.72 else "medium" if confidence >= 0.45 else "low"
    return round(confidence, 2), band


def _qa_response_cache_key(question: str, document_ids: list[str]) -> str:
    q_hash = hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()
    docs_hash = hashlib.sha256(",".join(sorted(document_ids)).encode("utf-8")).hexdigest()[:16]
    return f"qa:response:{QA_RESPONSE_CACHE_VERSION}:{docs_hash}:{q_hash}"


def _thread_cache_key(user_id: str, thread_id: str) -> str:
    return f"qa:thread:{user_id}:{thread_id}"


def _load_thread_context(user_id: str | None, thread_id: str | None) -> list[dict]:
    if not user_id or not thread_id:
        return []
    cache = get_cache_service()
    value = cache.get_json(_thread_cache_key(str(user_id), thread_id))
    if isinstance(value, list):
        return value[-settings.QA_THREAD_MAX_TURNS :]
    return []


def _save_thread_turn(user_id: str | None, thread_id: str | None, question: str, answer: str):
    if not user_id or not thread_id:
        return
    cache = get_cache_service()
    key = _thread_cache_key(str(user_id), thread_id)
    turns = cache.get_json(key)
    if not isinstance(turns, list):
        turns = []
    turns.append({"question": question, "answer": answer})
    turns = turns[-settings.QA_THREAD_MAX_TURNS :]
    cache.set_json(key, turns, ttl_seconds=settings.QA_THREAD_TTL_SECONDS)


def run_qa_pipeline_with_metadata_for_documents(
    question: str,
    document_ids: list[str],
    thread_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    unique_document_ids = []
    seen = set()
    for document_id in document_ids:
        key = str(document_id)
        if key and key not in seen:
            seen.add(key)
            unique_document_ids.append(key)

    if not unique_document_ids:
        return {
            "answer": "No relevant information found.",
            "query_type": "fact",
            "confidence": 0.0,
            "confidence_band": "low",
            "missing_information": ["No document IDs provided."],
            "evidence_count": 0,
            "citations": [],
            "thread_id": thread_id,
        }

    cache = get_cache_service()
    can_cache_response = thread_id is None
    cache_key = _qa_response_cache_key(question, unique_document_ids)
    if can_cache_response:
        cached_result = cache.get_json(cache_key)
        if isinstance(cached_result, dict) and cached_result.get("answer"):
            return cached_result

    query_type = _classify_query(question)
    thread_context = _load_thread_context(user_id=user_id, thread_id=thread_id)
    evidence = _build_evidence(question, unique_document_ids, query_type)
    if not evidence:
        result = {
            "answer": "No relevant information found.",
            "query_type": query_type,
            "confidence": 0.0,
            "confidence_band": "low",
            "missing_information": ["No indexed chunks found for the provided document(s)."],
            "evidence_count": 0,
            "citations": [],
            "thread_id": thread_id,
        }
        if can_cache_response:
            cache.set_json(cache_key, result, ttl_seconds=settings.QA_RESPONSE_CACHE_TTL_SECONDS)
        return result

    safe_evidence = []
    for item in evidence:
        safe_text = redact_text(item["text"])[0]
        safe_evidence.append(
            {
                "text": safe_text,
                "document_id": item.get("document_id"),
                "chunk_id": item.get("chunk_id"),
                "chunk_index": item.get("chunk_index"),
                "score": item.get("score"),
                "support_queries": item.get("support_queries", []),
            }
        )

    missing_info = _infer_missing_info(question, query_type, safe_evidence)
    prompt = build_reasoning_qa_prompt(
        question=question,
        query_type=query_type,
        context_chunks=safe_evidence,
        missing_info=missing_info,
        thread_context=thread_context,
    )

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
        ],
    )

    answer = response.choices[0].message.content or ""
    if _is_rejection_answer(answer) and _is_document_advice_question(question):
        answer = (
            "Your question is related to these document(s). Based on retrieved context, "
            "I can provide guidance, but some details needed for a strong recommendation "
            "may be missing. Ask a focused follow-up like policy type, premium, tenure, "
            "returns, risk profile, and goals to get a better recommendation."
        )

    confidence, confidence_band = _confidence_from_evidence(safe_evidence)
    citations = [
        {
            "evidence_id": f"EVIDENCE_{idx + 1}",
            "document_id": item.get("document_id"),
            "chunk_id": item.get("chunk_id"),
            "chunk_index": item.get("chunk_index"),
            "relevance_score": round(float(item.get("score", 0.0)), 2),
            "matched_queries": item.get("support_queries", [])[:2],
            "snippet": item.get("text", "")[:220],
        }
        for idx, item in enumerate(safe_evidence[:6])
    ]

    result = {
        "answer": answer,
        "query_type": query_type,
        "confidence": confidence,
        "confidence_band": confidence_band,
        "missing_information": missing_info,
        "evidence_count": len(safe_evidence),
        "document_ids": unique_document_ids,
        "citations": citations,
        "thread_id": thread_id,
    }

    if can_cache_response:
        cache.set_json(cache_key, result, ttl_seconds=settings.QA_RESPONSE_CACHE_TTL_SECONDS)

    _save_thread_turn(user_id=user_id, thread_id=thread_id, question=question, answer=answer)
    return result


def run_qa_pipeline_with_metadata(question: str, document_id: str) -> dict:
    return run_qa_pipeline_with_metadata_for_documents(question, [document_id])


def run_qa_pipeline_for_documents(
    question: str,
    document_ids: list[str],
    thread_id: str | None = None,
    user_id: str | None = None,
) -> str:
    result = run_qa_pipeline_with_metadata_for_documents(
        question=question,
        document_ids=document_ids,
        thread_id=thread_id,
        user_id=user_id,
    )
    return result["answer"]


def run_qa_pipeline(question: str, document_id: str) -> str:
    return run_qa_pipeline_for_documents(question=question, document_ids=[document_id])
