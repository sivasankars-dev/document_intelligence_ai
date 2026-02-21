from types import SimpleNamespace

from services.notification_service.fallback_engine import FallbackEngine
from workers.tasks.reminder_dispatcher import dispatch_reminder


class FakeDB:
    def __init__(self):
        self.commit_calls = 0

    def commit(self):
        self.commit_calls += 1


def test_get_next_channel_returns_next_item():
    engine = FallbackEngine()
    channels = ["email", "sms", "push"]

    assert engine.get_next_channel(channels, "email") == "sms"
    assert engine.get_next_channel(channels, "sms") == "push"


def test_get_next_channel_returns_none_for_last_or_unknown():
    engine = FallbackEngine()
    channels = ["email", "sms"]

    assert engine.get_next_channel(channels, "sms") is None
    assert engine.get_next_channel(channels, "push") is None


def test_dispatch_reminder_falls_back_to_next_enabled_channel(monkeypatch):
    reminder = SimpleNamespace(status="PENDING")
    user = SimpleNamespace(id="user-2", email="user@example.com")
    db = FakeDB()
    pref = SimpleNamespace(
        quiet_hours_start=None,
        quiet_hours_end=None,
        channel_priority=["email", "sms"],
        email_enabled=True,
        sms_enabled=True,
        push_enabled=False,
    )
    sent_channels = []

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.get_user_preferences",
        lambda _db, _user_id: pref,
    )

    def fake_send_notification(**kwargs):
        sent_channels.append(kwargs["channel"])
        if kwargs["channel"] == "email":
            raise RuntimeError("email failure")

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.notification_service.send_notification",
        fake_send_notification,
    )

    dispatch_reminder(reminder, user, db)

    assert sent_channels == ["email", "sms"]
    assert reminder.status == "SENT"
    assert db.commit_calls == 1
