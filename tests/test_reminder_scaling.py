import uuid
from types import SimpleNamespace

from workers.tasks.reminder_dispatcher import dispatch_due_reminders


class FakeDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_dispatch_due_reminders_processes_large_volume_once(monkeypatch):
    total = 1000
    batch_size = 200
    reminder_ids = [str(uuid.uuid4()) for _ in range(total)]
    batches = [
        [SimpleNamespace(id=rid) for rid in reminder_ids[i:i + batch_size]]
        for i in range(0, total, batch_size)
    ]
    batches.append([])

    fake_db = FakeDB()
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.SessionLocal",
        lambda: fake_db,
    )

    def fake_fetch_batch_for_processing(_db):
        return batches.pop(0)

    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher.ReminderRepository.fetch_batch_for_processing",
        fake_fetch_batch_for_processing,
    )

    processed = []
    monkeypatch.setattr(
        "workers.tasks.reminder_dispatcher._enqueue_reminder",
        lambda reminder_id: processed.append(reminder_id),
    )

    dispatch_due_reminders()

    assert len(processed) == total
    assert set(processed) == set(reminder_ids)
    assert fake_db.closed is True
