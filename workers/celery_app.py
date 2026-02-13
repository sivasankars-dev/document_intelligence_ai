from celery import Celery
from shared.config.settings import settings

celery_app = Celery(
    "life_admin_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks.ingestion_tasks"],
)

celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.task_routes = {
    "workers.tasks.ingestion_tasks.*": {"queue": "ingestion"}
}
