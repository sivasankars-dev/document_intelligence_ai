from types import SimpleNamespace

from services.extraction_service.extraction_pipeline import run_extraction_pipeline
from services.ingestion_service.ingestion_pipeline import run_ingestion_pipeline
from services.qa_service.qa_pipeline import run_qa_pipeline


class _FakeQuery:
    def __init__(self, document):
        self._document = document

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._document


class _FakeDB:
    def __init__(self, document):
        self._document = document

    def query(self, *args, **kwargs):
        return _FakeQuery(self._document)

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None

    def refresh(self, _obj):
        return None


def test_ingestion_stores_only_redacted_text(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        True,
    )
    fake_document = SimpleNamespace(
        id="doc-1",
        file_name="sample.pdf",
        storage_path="obj-key",
        document_status="uploaded",
    )
    monkeypatch.setattr(
        "services.ingestion_service.ingestion_pipeline.SessionLocal",
        lambda: _FakeDB(fake_document),
    )

    class _FakeStorage:
        def download_file(self, object_name, destination_path):
            return destination_path

    monkeypatch.setattr(
        "services.ingestion_service.ingestion_pipeline.StorageService",
        lambda: _FakeStorage(),
    )
    monkeypatch.setattr(
        "services.ingestion_service.ingestion_pipeline.extract_text_from_document",
        lambda _path: "Email john@example.com and SSN 123-45-6789",
    )

    captured = {}
    monkeypatch.setattr(
        "services.ingestion_service.ingestion_pipeline._store_document_chunks",
        lambda doc_id, text: captured.update({"doc_id": doc_id, "text": text}),
    )

    run_ingestion_pipeline("doc-1")

    assert captured["doc_id"] == "doc-1"
    assert "john@example.com" not in captured["text"]
    assert "123-45-6789" not in captured["text"]
    assert "[PII_EMAIL_1]" in captured["text"]
    assert "[PII_SSN_1]" in captured["text"]


def test_extraction_pipeline_redacts_before_llm(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "services.extraction_service.extraction_pipeline.SessionLocal",
        lambda: _FakeDB(None),
    )
    monkeypatch.setattr(
        "services.extraction_service.extraction_pipeline.retrieve_document_chunks",
        lambda query, document_id, top_k=5: [
            "Candidate email is john@example.com and SSN is 123-45-6789"
        ],
    )

    captured = {}

    def _fake_llm(prompt: str):
        captured["prompt"] = prompt
        return []

    monkeypatch.setattr(
        "services.extraction_service.extraction_pipeline.run_extraction_llm",
        _fake_llm,
    )
    monkeypatch.setattr(
        "services.extraction_service.extraction_pipeline.store_extracted_facts",
        lambda db, document_id, facts: None,
    )

    run_extraction_pipeline("doc-2")

    prompt = captured["prompt"]
    assert "john@example.com" not in prompt
    assert "123-45-6789" not in prompt
    assert "[PII_EMAIL_1]" in prompt
    assert "[PII_SSN_1]" in prompt


def test_qa_pipeline_redacts_before_openai(monkeypatch):
    monkeypatch.setattr(
        "services.privacy_service.pii_redactor.settings.PII_REDACTION_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "services.qa_service.qa_pipeline.retrieve_document_evidence",
        lambda query, document_id, top_k=6: [
            {
                "chunk_id": "doc-3:0:abc",
                "document_id": document_id,
                "chunk_index": 0,
                "text": "Contact: john@example.com and SSN: 123-45-6789",
                "distance": 0.2,
            }
        ],
    )
    monkeypatch.setattr(
        "services.qa_service.qa_pipeline.get_cache_service",
        lambda: SimpleNamespace(get_json=lambda _key: None, set_json=lambda *_args, **_kwargs: None),
    )

    captured = {}

    class _FakeCompletions:
        @staticmethod
        def create(model, messages):
            captured["messages"] = messages
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
            )

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    monkeypatch.setattr("services.qa_service.qa_pipeline.client", _FakeClient())

    answer = run_qa_pipeline("Is this candidate good?", "doc-3")
    assert answer == "ok"

    user_prompt = captured["messages"][1]["content"]
    assert "john@example.com" not in user_prompt
    assert "123-45-6789" not in user_prompt
    assert "[PII_EMAIL_1]" in user_prompt
    assert "[PII_SSN_1]" in user_prompt
