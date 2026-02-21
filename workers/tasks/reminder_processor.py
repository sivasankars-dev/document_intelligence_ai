from shared.database.session import SessionLocal
from shared.models.reminder import Reminder

try:
    from workers.celery_app import celery_app
except ModuleNotFoundError:
    celery_app = None

def _process_single_reminder_impl(self, reminder_id):
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).get(reminder_id)
        if not reminder or reminder.status != "PENDING":
            return
        # 🔔 Simulated Notification
        print(f"Sending reminder {reminder.id}")
        reminder.status = "SENT"
        db.commit()
    except Exception as e:
        reminder.retry_count += 1
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
