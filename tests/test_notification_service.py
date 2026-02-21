from datetime import datetime
from types import SimpleNamespace

import pytest

from services.notification_service.notification_service import NotificationService

def test_send_notification_email(monkeypatch):
    captured = []

    monkeypatch.setattr(
        "services.notification_service.notification_service.EmailProvider.send",
        lambda self, recipient, message: captured.append((recipient, message)),
    )

    service = NotificationService()
    reminder = SimpleNamespace(title="Policy Renewal", remind_at=datetime(2026, 3, 10, 9, 30, 0))

    service.send_notification("email", "user@example.com", reminder)

    assert captured == [(
        "user@example.com",
        "Reminder: Policy Renewal due on 2026-03-10 09:30:00",
    )]


def test_send_notification_sms(monkeypatch):
    captured = []

    monkeypatch.setattr(
        "services.notification_service.notification_service.SMSProvider.send",
        lambda self, recipient, message: captured.append((recipient, message)),
    )

    service = NotificationService()
    reminder = SimpleNamespace(title="Premium Payment", remind_at=datetime(2026, 3, 1, 8, 0, 0))

    service.send_notification("sms", "+15550001111", reminder)

    assert captured == [(
        "+15550001111",
        "Reminder: Premium Payment due on 2026-03-01 08:00:00",
    )]


def test_send_notification_push(monkeypatch):
    captured = []

    monkeypatch.setattr(
        "services.notification_service.notification_service.PushProvider.send",
        lambda self, recipient, message: captured.append((recipient, message)),
    )

    service = NotificationService()
    reminder = SimpleNamespace(title="Contract Deadline", remind_at=datetime(2026, 4, 5, 18, 15, 0))

    service.send_notification("push", "device-token-123", reminder)

    assert captured == [(
        "device-token-123",
        "Reminder: Contract Deadline due on 2026-04-05 18:15:00",
    )]


def test_send_notification_invalid_channel():
    service = NotificationService()
    reminder = SimpleNamespace(title="Any", remind_at=datetime(2026, 1, 1, 0, 0, 0))

    with pytest.raises(RuntimeError, match="Notification failed: Unsupported channel"):
        service.send_notification("fax", "someone", reminder)
