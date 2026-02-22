from services.notification_service.providers.email_provider import EmailProvider
from services.notification_service.providers.sms_provider import SMSProvider
from services.notification_service.providers.push_provider import PushProvider
from services.notification_service.notification_repository import NotificationRepository
from services.notification_service.notification_templates import build_reminder_message

class NotificationService:
    def __init__(self):
        self.email = EmailProvider()
        self.sms = SMSProvider()
        self.push = PushProvider()
        self.repository = NotificationRepository()

    def _resolve_provider(self, channel):
        if channel == "email":
            return self.email
        if channel == "sms":
            return self.sms
        if channel == "push":
            return self.push
        raise ValueError("Unsupported channel")

    def send_notification(self, channel, recipient, reminder, db=None):
        provider_message_id = None
        try:
            message = build_reminder_message(reminder)
            provider = self._resolve_provider(channel)
            result = provider.send(recipient, message)
            provider_message_id = result.get("message_id") if isinstance(result, dict) else None
            if db is not None:
                self.repository.save_log(
                    db=db,
                    reminder_id=reminder.id,
                    channel=channel,
                    recipient=recipient,
                    status="SENT",
                    provider_message_id=provider_message_id,
                )
            return {"status": "SENT", "provider_message_id": provider_message_id}
        except Exception as e:
            if db is not None and getattr(reminder, "id", None) is not None:
                try:
                    self.repository.save_log(
                        db=db,
                        reminder_id=reminder.id,
                        channel=channel,
                        recipient=recipient,
                        status="FAILED",
                        provider_message_id=provider_message_id,
                        error_message=str(e),
                    )
                except Exception:
                    pass
            raise RuntimeError(f"Notification failed: {str(e)}")
