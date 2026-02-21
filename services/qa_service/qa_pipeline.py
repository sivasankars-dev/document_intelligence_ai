from openai import OpenAI
from shared.config.settings import settings

from services.qa_service.retriever_service import retrieve_document_chunks
from services.qa_service.prompt_service import build_qa_prompt
from services.privacy_service.pii_redactor import redact_text

client = OpenAI(api_key=settings.OPENAI_API_KEY)


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


def run_qa_pipeline(question: str, document_id: str):
    # Retrieve chunks
    chunks = retrieve_document_chunks(question, document_id)

    if not chunks:
        return "No relevant information found."

    # Build prompt
    safe_chunks = [redact_text(chunk)[0] for chunk in chunks]
    prompt = build_qa_prompt(question, safe_chunks)

    # Call LLM
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
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content or ""
    if _is_rejection_answer(answer) and _is_document_advice_question(question):
        return (
            "Your question is related to this document. Based on retrieved context, "
            "I can provide guidance, but some details needed for a strong recommendation "
            "may be missing. Ask a focused follow-up like policy type, premium, tenure, "
            "returns, risk profile, and goals to get a better recommendation."
        )

    return answer
