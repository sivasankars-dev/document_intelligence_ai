from openai import OpenAI
from shared.config.settings import settings

from services.qa_service.retriever_service import retrieve_document_chunks
from services.qa_service.prompt_service import build_qa_prompt

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def run_qa_pipeline(question: str, document_id: str):
    # Retrieve chunks
    chunks = retrieve_document_chunks(question, document_id)

    if not chunks:
        return "No relevant information found."

    # Build prompt
    prompt = build_qa_prompt(question, chunks)

    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document QA assistant. "
                    "Only reply 'Please ask about document.' for truly unrelated questions."
                ),
            },
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
