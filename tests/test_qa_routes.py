from fastapi.testclient import TestClient

from gateway.dependencies.auth import get_current_user
from gateway.main import app

client = TestClient(app)


def override_get_current_user():
    return {"user_id": "test-user-id", "email": "qa@test.com", "token": "test-token"}


def test_ask_question_success(monkeypatch):
    app.dependency_overrides[get_current_user] = override_get_current_user
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
