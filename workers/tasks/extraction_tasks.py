try:
    from workers.celery_app import celery_app
except ModuleNotFoundError:
    celery_app = None


def _run_pipeline(document_id: str):
    from services.extraction_service.extraction_pipeline import run_extraction_pipeline

    run_extraction_pipeline(document_id)


if celery_app is not None:
    @celery_app.task
    def extract_document_facts(document_id: str):
        _run_pipeline(document_id)
else:
    def extract_document_facts(document_id: str):
        _run_pipeline(document_id)
