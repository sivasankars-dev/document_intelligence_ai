import hashlib

import httpx

from shared.config.settings import settings
from services.notification_service.providers.base_provider import BaseNotificationProvider


class SMSProvider(BaseNotificationProvider):
    def send(self, recipient: str, message: str) -> dict:
        message_id = hashlib.sha1(f"sms:{recipient}:{message}".encode("utf-8")).hexdigest()[:16]
        if settings.NOTIFICATION_DRY_RUN:
            return {"provider": "sms", "message_id": message_id, "status": "sent"}

        if not settings.SMS_PROVIDER_URL:
            raise RuntimeError("SMS_PROVIDER_URL is required for SMS notifications")

        headers = {}
        if settings.SMS_PROVIDER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.SMS_PROVIDER_TOKEN}"

        response = httpx.post(
            settings.SMS_PROVIDER_URL,
            json={"to": recipient, "message": message},
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        return {"provider": "sms", "message_id": message_id, "status": "sent"}
