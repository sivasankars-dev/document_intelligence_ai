from datetime import datetime
from types import SimpleNamespace
from services.notification_service.preference_engine import PreferenceEngine
from workers.tasks.reminder_dispatcher import dispatch_reminder

class _FixedDateTime:
    @staticmethod
    def utcnow():
        return datetime(2026, 2, 15, 22, 0, 0)

    @staticmethod
    def strptime(value, fmt):
        return datetime.strptime(value, fmt)

class FakeDB:
    def __init__(self):
        self.commit_calls = 0

    def commit(self):
        self.commit_calls += 1


def test_is_within_quiet_hours_true(monkeypatch):
    monkeypatch.setattr(
        "services.notification_service.preference_engine.datetime",
        _FixedDateTime,
    )
    pref = SimpleNamespace(quiet_hours_start="21:00", quiet_hours_end="23:00")

    engine = PreferenceEngine()

    assert engine.is_within_quiet_hours(pref) is True


def test_dispatch_reminder_skips_during_quiet_hours(monkeypatch):
    reminder = SimpleNamespace(status="PENDING")
    user = SimpleNamespace(id="user-1", email="user@example.com")
    db = FakeDB()
    calls = []
    pref = SimpleNamespace(
        quiet_hours_start="21:00",
        quiet_hours_end="23:00",
        channel_priority=["email", "sms"],
        email_enabled=True,
        sms_enabled=True,
        push_enabled=False,
    )

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.get_user_preferences",
        lambda _db, _user_id: pref,
    )
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.preference_engine.is_within_quiet_hours",
        lambda _pref: True,
    )
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.notification_service.send_notification",
        lambda **kwargs: calls.append(kwargs),
    )

    dispatch_reminder(reminder, user, db)

    assert calls == []
    assert reminder.status == "PENDING"
    assert db.commit_calls == 0
