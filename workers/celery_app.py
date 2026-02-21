from celery import Celery

from shared.config.settings import settings

celery_app = Celery(
    "life_admin_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.tasks.ingestion_tasks",
        "workers.tasks.extraction_tasks",
        "workers.tasks.reminder_dispatcher",
        "workers.tasks.reminder_processor",
    ],
)

celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.task_routes = {
    "workers.tasks.ingestion_tasks.*": {"queue": "ingestion"},
    "workers.tasks.extraction_tasks.*": {"queue": "extraction"},
    "workers.tasks.reminder_dispatcher.*": {"queue": "reminders"},
    "workers.tasks.reminder_processor.*": {"queue": "reminders"},
}

celery_app.conf.beat_schedule = {
    "dispatch-reminders-every-minute": {
        "task": "workers.tasks.reminder_dispatcher.dispatch_due_reminders",
        "schedule": 60.0,
    }
}
