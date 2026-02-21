import uuid
from sqlalchemy import Column, Text, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from shared.database.base import Base

class Risk(Base):
    __tablename__ = "risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False
    )
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=True)
    detected_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
