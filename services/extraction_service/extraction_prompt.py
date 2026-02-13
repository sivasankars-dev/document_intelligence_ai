def build_extraction_prompt(context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks)

    return f"""
    You are an AI document analysis expert.

    Extract important structured facts from the document.

    Return ONLY JSON in this format:

    [
    {{
        "key": "fact_name",
        "value": "fact_value",
        "confidence_score": 0.0 to 1.0
    }}
    ]

    DOCUMENT:
    {context}
    """