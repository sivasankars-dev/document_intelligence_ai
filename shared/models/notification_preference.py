from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from shared.database.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    channel_priority = Column(JSON, default=["email", "push", "sms"])
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(String, nullable=True)
    quiet_hours_end = Column(String, nullable=True)
