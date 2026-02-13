from workers.celery_app import celery_app
from services.ingestion_service.ingestion_pipeline import run_ingestion_pipeline


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=5) 
def ingest_document_task(self, document_id: str):
    run_ingestion_pipeline(document_id)
