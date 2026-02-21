from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.database.base import Base


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=True)
    source_chunk_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
