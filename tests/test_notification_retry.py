from types import SimpleNamespace

from services.notification_service.retry_engine import RetryEngine
from workers.tasks.reminder_dispatcher import dispatch_reminder


class FakeDB:
    def __init__(self):
        self.commit_calls = 0

    def commit(self):
        self.commit_calls += 1


def test_failure_triggers_retry(monkeypatch):
    reminder = SimpleNamespace(
        id="rem-1",
        status="PENDING",
        retry_count=0,
        max_retries=3,
        last_error=None,
    )
    user = SimpleNamespace(id="user-1", email="user@example.com", preferred_channel="email")
    db = FakeDB()

    def fail_send(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.notification_service.send_notification",
        fail_send,
    )
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.get_user_preferences",
        lambda _db, _user_id: None,
    )

    dispatch_reminder(reminder, user, db)

    assert reminder.status == "PENDING"
    assert reminder.retry_count == 1
    assert reminder.last_error == "provider down"
    assert db.commit_calls == 1


def test_max_retry_moves_to_dead_letter(monkeypatch):
    reminder = SimpleNamespace(
        id="rem-2",
        status="PENDING",
        retry_count=3,
        max_retries=3,
        last_error=None,
    )
    user = SimpleNamespace(id="user-2", email="user@example.com", preferred_channel="email")
    db = FakeDB()

    def fail_send(*args, **kwargs):
        raise RuntimeError("hard failure")

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.notification_service.send_notification",
        fail_send,
    )
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.get_user_preferences",
        lambda _db, _user_id: None,
    )

    dispatch_reminder(reminder, user, db)

    assert reminder.status == "DEAD_LETTER"
    assert reminder.retry_count == 4
    assert reminder.last_error == "hard failure"
    assert db.commit_calls == 1


def test_retry_engine_increment_counter():
    reminder = SimpleNamespace(retry_count=0, max_retries=3, last_error=None)
    engine = RetryEngine()

    assert engine.should_retry(reminder) is True
    engine.increment_retry(reminder, "temporary failure")

    assert reminder.retry_count == 1
    assert reminder.last_error == "temporary failure"
