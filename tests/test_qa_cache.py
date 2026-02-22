from types import SimpleNamespace
import sys

from services.qa_service.qa_pipeline import run_qa_pipeline_with_metadata
from services.qa_service.retriever_service import retrieve_document_chunks


class _FakeCache:
    def __init__(self):
        self.store = {}

    def get_json(self, key):
        return self.store.get(key)

    def set_json(self, key, value, ttl_seconds):
        self.store[key] = value


def test_retriever_uses_cache(monkeypatch):
    fake_cache = _FakeCache()
    monkeypatch.setattr(
        "services.qa_service.retriever_service.get_cache_service",
        lambda: fake_cache,
    )

    calls = {"count": 0}

    def _fake_query(**_kwargs):
        calls["count"] += 1
        return {"documents": [["chunk-1", "chunk-2"]]}

    fake_vector_service = SimpleNamespace(
        embeddings=SimpleNamespace(embed_query=lambda _query: [0.11, 0.22]),
        collection=SimpleNamespace(query=_fake_query),
    )
    monkeypatch.setitem(sys.modules, "services.extraction_service.vector_service", fake_vector_service)

    first = retrieve_document_chunks("What is premium?", "doc-1", top_k=5)
    second = retrieve_document_chunks("What is premium?", "doc-1", top_k=5)

    assert first == ["chunk-1", "chunk-2"]
    assert second == ["chunk-1", "chunk-2"]
    assert calls["count"] == 1


def test_qa_pipeline_uses_response_cache(monkeypatch):
    fake_cache = _FakeCache()
    monkeypatch.setattr(
        "services.qa_service.qa_pipeline.get_cache_service",
        lambda: fake_cache,
    )
    monkeypatch.setattr(
        "services.qa_service.qa_pipeline.retrieve_document_evidence",
        lambda query, document_id, top_k=6: [
            {
                "chunk_id": f"{document_id}:0:abc",
                "document_id": document_id,
                "chunk_index": 0,
                "text": "Policy has premium and due date clauses.",
                "distance": 0.2,
            }
        ],
    )

    calls = {"count": 0}

    class _FakeCompletions:
        @staticmethod
        def create(model, messages):
            calls["count"] += 1
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Answer from model"))]
            )

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    monkeypatch.setattr("services.qa_service.qa_pipeline.client", _FakeClient())

    first = run_qa_pipeline_with_metadata("What are problems?", "doc-2")
    second = run_qa_pipeline_with_metadata("What are problems?", "doc-2")

    assert first["answer"] == "Answer from model"
    assert second["answer"] == "Answer from model"
    assert calls["count"] == 1
