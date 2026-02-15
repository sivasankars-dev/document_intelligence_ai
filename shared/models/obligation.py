import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    DateTime,
    Date,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from shared.database.base import Base


class Obligation(Base):
    __tablename__ = "obligations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    recurrence = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    detected_by = Column(String, nullable=True)
    source_text = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
