import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from shared.database.base import Base

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    obligation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("obligations.id"),
        nullable=False
    )
    remind_at = Column(DateTime, nullable=False)
    status = Column(String, default="PENDING")
    channel = Column(String, default="IN_APP")
    retry_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
