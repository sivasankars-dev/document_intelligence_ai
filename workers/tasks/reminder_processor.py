from shared.database.session import SessionLocal
from shared.models.reminder import Reminder
from workers.tasks.reminder_tasks import _get_user_for_reminder

try:
    from workers.celery_app import celery_app
except ModuleNotFoundError:
    celery_app = None

def _process_single_reminder_impl(self, reminder_id):
    db = SessionLocal()
    try:
        reminder = db.get(Reminder, reminder_id)
        if not reminder or reminder.status != "PENDING":
            return
        from workers.tasks.reminder_dispatcher import dispatch_reminder

        user = _get_user_for_reminder(db, reminder)
        if user is None:
            reminder.status = "DEAD_LETTER"
            reminder.last_error = "User not found for reminder obligation"
            db.commit()
            return

        dispatch_reminder(reminder, user, db)
    except Exception as e:
        if reminder is not None:
            reminder.retry_count = (reminder.retry_count or 0) + 1
            reminder.last_error = str(e)
            db.commit()
        if self is not None:
            raise self.retry(exc=e, countdown=30)
        raise
    finally:
        db.close()


if celery_app is not None:
    @celery_app.task(bind=True, max_retries=3)
    def process_single_reminder(self, reminder_id):
        _process_single_reminder_impl(self, reminder_id)
else:
    class _ProcessSingleReminderProxy:
        def __call__(self, reminder_id):
            _process_single_reminder_impl(None, reminder_id)

        @staticmethod
        def delay(reminder_id):
            _process_single_reminder_impl(None, reminder_id)

    process_single_reminder = _ProcessSingleReminderProxy()
