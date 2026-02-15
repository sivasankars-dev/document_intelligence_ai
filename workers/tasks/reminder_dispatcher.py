from shared.database.session import SessionLocal
from services.obligation_service.reminder_repository import ReminderRepository
from workers.tasks.reminder_processor import process_single_reminder

try:
    from workers.celery_app import celery_app
except ModuleNotFoundError:
    celery_app = None


def _enqueue_reminder(reminder_id: str):
    process_single_reminder.delay(reminder_id)


def _dispatch_due_reminders_impl():
    db = SessionLocal()
    try:
        while True:
            reminders = ReminderRepository.fetch_batch_for_processing(db)
            if not reminders:
                break

            for reminder in reminders:
                _enqueue_reminder(str(reminder.id))
    finally:
        db.close()


if celery_app is not None:
    @celery_app.task
    def dispatch_due_reminders():
        _dispatch_due_reminders_impl()
else:
    def dispatch_due_reminders():
        _dispatch_due_reminders_impl()
