from datetime import datetime

from shared.database.session import SessionLocal
from services.obligation_service.reminder_repository import ReminderRepository
from shared.models.reminder import Reminder
from shared.models.obligation import Obligation
from shared.models.user import User

try:
    from workers.celery_app import celery_app
except ModuleNotFoundError:
    celery_app = None


def _get_user_for_reminder(db, reminder):
    if reminder is None:
        return None
    return (
        db.query(User)
        .join(Obligation, Obligation.user_id == User.id)
        .filter(Obligation.id == reminder.obligation_id)
        .first()
    )

def _process_due_reminders_impl():
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


def _retry_reminder_task_impl(reminder_id):
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).get(reminder_id)
        user = _get_user_for_reminder(db, reminder)
        if reminder is None or user is None:
            return

        # Import here to avoid circular dependency with reminder_dispatcher.
        from workers.tasks.reminder_dispatcher import dispatch_reminder

        dispatch_reminder(reminder, user, db)
    finally:
        db.close()


if celery_app is not None:
    @celery_app.task
    def process_due_reminders():
        _process_due_reminders_impl()

    @celery_app.task(bind=True, max_retries=5)
    def retry_reminder_task(self, reminder_id):
        _retry_reminder_task_impl(reminder_id)
else:
    def process_due_reminders():
        _process_due_reminders_impl()

    class _RetryReminderProxy:
        def __call__(self, reminder_id):
            _retry_reminder_task_impl(reminder_id)

        @staticmethod
        def delay(reminder_id):
            _retry_reminder_task_impl(reminder_id)

    retry_reminder_task = _RetryReminderProxy()
