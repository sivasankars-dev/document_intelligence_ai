import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    description: str
    severity: str
    confidence_score: float | None = None
    detected_by: str | None = None
    created_at: datetime | None = None
