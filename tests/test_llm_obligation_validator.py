import pytest
from services.obligation_service.llm_validator import validate_obligation

@pytest.mark.asyncio
async def test_llm_validator():
    sentence = "Premium must be paid before 10 March 2026"

    result = await validate_obligation(sentence)

    assert result is not None
    assert result.title is not None
