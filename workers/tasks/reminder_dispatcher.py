from shared.database.session import SessionLocal
from shared.config.settings import settings
from services.obligation_service.reminder_repository import ReminderRepository
from workers.tasks.reminder_processor import process_single_reminder
from services.notification_service.notification_service import NotificationService
from services.notification_service.retry_engine import RetryEngine
from workers.tasks.reminder_tasks import retry_reminder_task
from services.notification_service.preference_engine import PreferenceEngine
from services.notification_service.fallback_engine import FallbackEngine
from services.notification_service.preference_repository import get_user_preferences

notification_service = NotificationService()
retry_engine = RetryEngine()
preference_engine = PreferenceEngine()
fallback_engine = FallbackEngine()
notification_service = NotificationService()

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

def dispatch_reminder(reminder, user, db):
    pref = get_user_preferences(db, user.id)
    if not pref:
        channels = ["email"]
    else:
        if preference_engine.is_within_quiet_hours(pref):
            print("Skipping reminder — quiet hours")
            return
        channels = preference_engine.get_enabled_channels(pref)
    if not channels:
        channels = ["email"]

    last_error = None
    for channel in channels:
        try:
            notification_service.send_notification(
                channel=channel,
                recipient=user.email,
                reminder=reminder,
                db=db,
            )
            reminder.channel = channel.upper()
            reminder.status = "SENT"
            reminder.last_error = None
            db.commit()
            return
        except Exception as e:
            last_error = str(e)
            print(f"Channel {channel} failed: {e}")

    retry_engine.increment_retry(reminder, last_error or "Unknown notification error")
    if retry_engine.should_retry(reminder):
        reminder.status = "PENDING"
        db.commit()
        if settings.NOTIFICATION_AUTO_RETRY:
            retry_reminder_task.delay(str(reminder.id))
        return

    reminder.status = "DEAD_LETTER"
    db.commit()

if celery_app is not None:
    @celery_app.task
    def dispatch_due_reminders():
        _dispatch_due_reminders_impl()
else:
    def dispatch_due_reminders():
        _dispatch_due_reminders_impl()
