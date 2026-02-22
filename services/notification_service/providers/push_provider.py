import hashlib

import httpx

from shared.config.settings import settings
from services.notification_service.providers.base_provider import BaseNotificationProvider


class PushProvider(BaseNotificationProvider):
    def send(self, recipient: str, message: str) -> dict:
        message_id = hashlib.sha1(f"push:{recipient}:{message}".encode("utf-8")).hexdigest()[:16]
        if settings.NOTIFICATION_DRY_RUN:
            return {"provider": "push", "message_id": message_id, "status": "sent"}

        if not settings.PUSH_PROVIDER_URL:
            raise RuntimeError("PUSH_PROVIDER_URL is required for push notifications")

        headers = {}
        if settings.PUSH_PROVIDER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.PUSH_PROVIDER_TOKEN}"

        response = httpx.post(
            settings.PUSH_PROVIDER_URL,
            json={"to": recipient, "message": message},
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        return {"provider": "push", "message_id": message_id, "status": "sent"}
