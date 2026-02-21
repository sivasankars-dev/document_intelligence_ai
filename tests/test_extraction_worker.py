from workers.tasks.extraction_tasks import extract_document_facts


def test_extraction_worker_calls_pipeline(monkeypatch):
    called = {}

    def fake_run_pipeline(document_id: str):
        called["document_id"] = document_id

    monkeypatch.setattr(
        "workers.tasks.extraction_tasks._run_pipeline",
        fake_run_pipeline,
    )

    document_id = "test-document-id"
    extract_document_facts(document_id)

    assert called["document_id"] == document_id
