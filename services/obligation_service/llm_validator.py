from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from services.obligation_service.schemas import ObligationStructured
from shared.config.settings import settings


# ---------------------------
# Initialize LLM
# ---------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY,
)


# ---------------------------
# Prompt Template
# ---------------------------
prompt = ChatPromptTemplate.from_template(
    """
Extract obligation details from the sentence.

Return ONLY valid JSON with structure:
{{
    "title": string,
    "due_date": ISO date string or null,
    "confidence_score": float between 0 and 1
}}

Sentence:
{sentence}
"""
)


# ---------------------------
# Validator Function
# ---------------------------
async def validate_obligation(sentence: str) -> ObligationStructured | None:
    """
    Validate and structure obligation using LLM
    """

    try:
        chain = prompt | llm.with_structured_output(ObligationStructured)

        result = await chain.ainvoke({"sentence": sentence})

        return result

    except Exception as e:
        print(f"LLM validation failed: {e}")
        return None
