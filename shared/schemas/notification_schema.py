from pydantic import BaseModel, Field


class NotificationPreferenceUpdate(BaseModel):
    channel_priority: list[str] | None = Field(default=None)
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


class NotificationPreferenceResponse(BaseModel):
    channel_priority: list[str]
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
