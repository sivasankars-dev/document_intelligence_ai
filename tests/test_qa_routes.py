from types import SimpleNamespace

from fastapi.testclient import TestClient

from gateway.dependencies.auth import get_current_user
from gateway.main import app
from shared.database.session import get_db

client = TestClient(app)


def override_get_current_user():
    return {"user_id": "test-user-id", "email": "qa@test.com", "token": "test-token"}


class _FakeQuery:
    def __init__(self, document):
        self.document = document

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.document


class _FakeDB:
    def __init__(self, document):
        self.document = document

    def query(self, *args, **kwargs):
        return _FakeQuery(self.document)


def _override_get_db_owned():
    yield _FakeDB(SimpleNamespace(id="doc", user_id="test-user-id"))


def _override_get_db_other_owner():
    yield _FakeDB(SimpleNamespace(id="doc", user_id="other-user-id"))


def test_ask_question_success(monkeypatch):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db_owned
    monkeypatch.setattr(
        "gateway.api.v1.qa_routes.run_qa_pipeline",
        lambda question, document_id: "This is a mocked answer.",
    )

    response = client.post(
        "/api/v1/qa/ask",
        json={
            "question": "What is my backend experience?",
            "document_id": "4af7a36f-a262-43e8-bc78-376cbe94383e",
        },
    )

    try:
        assert response.status_code == 200
        assert response.json() == {"answer": "This is a mocked answer."}
    finally:
        app.dependency_overrides.clear()


def test_ask_question_no_relevant_info(monkeypatch):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db_owned
    monkeypatch.setattr(
        "gateway.api.v1.qa_routes.run_qa_pipeline",
        lambda question, document_id: "No relevant information found.",
    )

    response = client.post(
        "/api/v1/qa/ask",
        json={
            "question": "When is insurance renewal?",
            "document_id": "4af7a36f-a262-43e8-bc78-376cbe94383e",
        },
    )

    try:
        assert response.status_code == 200
        assert response.json() == {"answer": "No relevant information found."}
    finally:
        app.dependency_overrides.clear()


def test_ask_question_with_reasoning(monkeypatch):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db_owned
    monkeypatch.setattr(
        "gateway.api.v1.qa_routes.run_qa_pipeline_with_metadata",
        lambda question, document_id: {
            "answer": "Reasoned answer",
            "query_type": "analysis",
            "confidence": 0.81,
            "confidence_band": "high",
            "missing_information": [],
            "evidence_count": 3,
            "citations": [],
        },
    )

    response = client.post(
        "/api/v1/qa/ask",
        json={
            "question": "what are the problems in this document?",
            "document_id": "4af7a36f-a262-43e8-bc78-376cbe94383e",
            "include_reasoning": True,
        },
    )

    try:
        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"] == "Reasoned answer"
        assert payload["query_type"] == "analysis"
        assert payload["confidence_band"] == "high"
    finally:
        app.dependency_overrides.clear()


def test_ask_question_forbidden_when_document_not_owned():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db_other_owner

    response = client.post(
        "/api/v1/qa/ask",
        json={
            "question": "What is my backend experience?",
            "document_id": "4af7a36f-a262-43e8-bc78-376cbe94383e",
        },
    )

    try:
        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have access to this document"
    finally:
        app.dependency_overrides.clear()
