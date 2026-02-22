from types import SimpleNamespace

from fastapi.testclient import TestClient

from gateway.dependencies.auth import get_current_user
from gateway.main import app
from shared.database.session import get_db

client = TestClient(app)


def override_get_current_user():
    return {"user_id": "user-1", "email": "u@example.com", "token": "token"}


class _FakeQuery:
    def __init__(self, document):
        self.document = document

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.document


class _FakeDB:
    def query(self, *args, **kwargs):
        return _FakeQuery(SimpleNamespace(user_id="user-1"))


def override_get_db():
    yield _FakeDB()


def test_get_document_risks(monkeypatch):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        "gateway.api.v1.risk_routes.RiskRepository.get_by_document",
        lambda db, document_id: [
            SimpleNamespace(
                id="5f9f8bc0-3529-4d8a-9ba0-82be892f3f93",
                document_id=document_id,
                description="Termination penalty clause detected.",
                severity="HIGH",
                confidence_score=0.86,
                detected_by="rule_engine",
                created_at=None,
            )
        ],
    )

    response = client.get("/api/v1/risks/document/4af7a36f-a262-43e8-bc78-376cbe94383e")
    try:
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["severity"] == "HIGH"
    finally:
        app.dependency_overrides.clear()
