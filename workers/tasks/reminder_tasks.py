from datetime import datetime

from workers.celery_app import celery_app
from shared.database.session import SessionLocal
from services.obligation_service.reminder_repository import ReminderRepository


@celery_app.task
def process_due_reminders():
    db = SessionLocal()
    try:
        reminders = ReminderRepository.get_pending_reminders(
            db,
            datetime.utcnow()
        )
        for reminder in reminders:
            print(f"Trigger reminder {reminder.id}")

            reminder.status = "SENT"

        db.commit()
    finally:
        db.close()
