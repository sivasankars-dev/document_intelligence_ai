import hashlib
import smtplib
from email.message import EmailMessage

from shared.config.settings import settings
from services.notification_service.providers.base_provider import BaseNotificationProvider


class EmailProvider(BaseNotificationProvider):
    def send(self, recipient: str, message: str) -> dict:
        message_id = hashlib.sha1(f"email:{recipient}:{message}".encode("utf-8")).hexdigest()[:16]
        if settings.NOTIFICATION_DRY_RUN:
            return {"provider": "email", "message_id": message_id, "status": "sent"}

        if not settings.SMTP_HOST:
            raise RuntimeError("SMTP_HOST is required for email notifications")

        email_message = EmailMessage()
        email_message["From"] = settings.NOTIFICATION_EMAIL_FROM
        email_message["To"] = recipient
        email_message["Subject"] = "Reminder Notification"
        email_message.set_content(message)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(email_message)

        return {"provider": "email", "message_id": message_id, "status": "sent"}
