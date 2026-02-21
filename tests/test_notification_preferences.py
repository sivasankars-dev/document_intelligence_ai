from types import SimpleNamespace

from services.notification_service.preference_engine import PreferenceEngine
from workers.tasks.reminder_dispatcher import dispatch_reminder


class FakeDB:
    def __init__(self):
        self.commit_calls = 0

    def commit(self):
        self.commit_calls += 1


def test_get_enabled_channels_respects_priority_and_flags():
    pref = SimpleNamespace(
        channel_priority=["sms", "push", "email"],
        email_enabled=True,
        sms_enabled=False,
        push_enabled=True,
    )
    engine = PreferenceEngine()

    assert engine.get_enabled_channels(pref) == ["push", "email"]


def test_dispatch_reminder_defaults_to_email_when_no_preferences(monkeypatch):
    reminder = SimpleNamespace(status="PENDING")
    user = SimpleNamespace(id="user-3", email="user@example.com")
    db = FakeDB()
    calls = []

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.get_user_preferences",
        lambda _db, _user_id: None,
    )
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.notification_service.send_notification",
        lambda **kwargs: calls.append(kwargs["channel"]),
    )

    dispatch_reminder(reminder, user, db)

    assert calls == ["email"]
    assert reminder.status == "SENT"
    assert db.commit_calls == 1
