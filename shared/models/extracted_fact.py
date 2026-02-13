from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid

from shared.database.base import Base


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
