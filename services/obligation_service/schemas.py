from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ObligationCandidate(BaseModel):
    """Represents rule-based extracted candidate sentence"""
    sentence: str = Field(..., description="Sentence containing possible obligation")


class ObligationStructured(BaseModel):
    """Final structured obligation validated by LLM"""

    title: str = Field(..., min_length=3, max_length=255)
    due_date: Optional[datetime] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ObligationCreate(BaseModel):
    document_id: str
    title: str
    due_date: Optional[datetime]
    confidence_score: float
