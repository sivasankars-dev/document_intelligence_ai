import uuid
from datetime import datetime
from types import SimpleNamespace

from services.obligation_service.reminder_generator import ReminderGenerator


def test_generate_reminders_creates_default_offsets(monkeypatch):
    obligation = SimpleNamespace(
        id=uuid.uuid4(),
        due_date=datetime(2026, 3, 10, 12, 0, 0),
    )
    created = []

    monkeypatch.setattr(
        "services.obligation_service.reminder_generator.ReminderRepository.create",
        lambda db, reminder: created.append(reminder),
    )

    ReminderGenerator.generate(db=object(), obligation=obligation)

    assert len(created) == 3
    assert [r.remind_at for r in created] == [
        datetime(2026, 2, 8, 12, 0, 0),
        datetime(2026, 3, 3, 12, 0, 0),
        datetime(2026, 3, 9, 12, 0, 0),
    ]


def test_generate_reminders_skips_when_no_due_date(monkeypatch):
    obligation = SimpleNamespace(id=uuid.uuid4(), due_date=None)
    created = []

    monkeypatch.setattr(
        "services.obligation_service.reminder_generator.ReminderRepository.create",
        lambda db, reminder: created.append(reminder),
    )

    ReminderGenerator.generate(db=object(), obligation=obligation)

    assert created == []
