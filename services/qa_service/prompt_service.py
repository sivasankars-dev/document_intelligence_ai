def build_qa_prompt(question: str, context_chunks: list[str]) -> str:
    context_text = "\n\n".join(context_chunks)

    prompt = f"""
    You are an intelligent document assistant.

    Follow these rules strictly:
    1. Use only the provided DOCUMENT CONTEXT.
    2. If the question is about this document (summary, strengths, weaknesses, hiring fit, risks, quality, recommendation),
       answer using the context and provide practical advice.
    3. If exact facts are missing, still provide cautious advice based on available context and clearly state assumptions.
    4. Respond with exactly "Please ask about document." only when the question is unrelated to this document
       (example: weather, cricket score, unrelated coding problem).
    5. Never reject a question that is clearly about evaluating the document.

    DOCUMENT CONTEXT:
    {context_text}

    QUESTION:
    {question}

    ANSWER:
    """

    return prompt
