from services.notification_service.providers.email_provider import EmailProvider
from services.notification_service.providers.sms_provider import SMSProvider
from services.notification_service.providers.push_provider import PushProvider
from services.notification_service.notification_templates import build_reminder_message

class NotificationService:
    def __init__(self):
        self.email = EmailProvider()
        self.sms = SMSProvider()
        self.push = PushProvider()

    def send_notification(self, channel, recipient, reminder):
        try:
            message = build_reminder_message(reminder)
            if channel == "email":
                self.email.send(recipient, message)
            elif channel == "sms":
                self.sms.send(recipient, message)
            elif channel == "push":
                self.push.send(recipient, message)
            else:
                raise ValueError("Unsupported channel")
        except Exception as e:  
            raise RuntimeError(f"Notification failed: {str(e)}")

