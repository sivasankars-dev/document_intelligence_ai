def build_qa_prompt(question: str, context_chunks: list[str]) -> str:
    context_text = "\n\n".join(context_chunks)

    prompt = f"""
    You are an intelligent document assistant.

    Follow these rules strictly:
    1. Base your answer primarily on the DOCUMENT CONTEXT.
    2. If the question is about evaluating this document (fit, strengths, weaknesses, risks, recommendation, comparison),
       provide practical advice grounded in the context.
    3. If exact facts are missing, do not reject. Give cautious guidance, state assumptions, and mention what is missing.
    4. Respond with exactly "Please ask about document." only when the question is clearly unrelated to this document
       (example: weather, sports score, random coding task).
    5. A question can still be document-related even if it asks for recommendation vs alternatives
       (example: "Should I take this policy or choose index funds?"). Do not reject these.

    DOCUMENT CONTEXT:
    {context_text}

    QUESTION:
    {question}

    ANSWER:
    """

    return prompt


def build_reasoning_qa_prompt(
    question: str,
    query_type: str,
    context_chunks: list[dict],
    missing_info: list[str],
    thread_context: list[dict] | None = None,
) -> str:
    context_text = "\n\n".join([
        (
            f"[EVIDENCE_{idx + 1}] "
            f"(document_id={chunk.get('document_id')}, chunk_id={chunk.get('chunk_id')}) "
            f"{chunk.get('text', '')}"
        )
        for idx, chunk in enumerate(context_chunks)
    ])
    missing_text = ", ".join(missing_info) if missing_info else "None identified"
    thread_text = "No prior thread context."
    if thread_context:
        thread_text = "\n".join(
            [
                f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}"
                for turn in thread_context
            ]
        )

    prompt = f"""
    You are a document reasoning assistant.

    Query type: {query_type}

    Rules:
    1. Base your answer on evidence snippets only.
    2. If evidence is incomplete, state assumptions and what is missing.
    3. Do not refuse unless clearly unrelated to this document.
    4. For comparison/recommendation queries, provide trade-offs.
    5. Cite evidence IDs inline like [EVIDENCE_2].
    6. If prior thread context exists, use it only to clarify follow-up intent.
       Never override current evidence with thread memory.

    Missing info hints: {missing_text}

    PRIOR THREAD CONTEXT:
    {thread_text}

    DOCUMENT EVIDENCE:
    {context_text}

    USER QUESTION:
    {question}

    ANSWER:
    """

    return prompt
