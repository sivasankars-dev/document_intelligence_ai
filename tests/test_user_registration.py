import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from gateway.main import app
from services.auth_service.auth_service import get_auth_service
from shared.database.session import get_db

client = TestClient(app)

class FakeAuthService:
    def create_user(self, db, email: str, password: str):
        return SimpleNamespace(
            id=uuid.uuid4(),
            email=email,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )


def override_get_db():
    yield object()


def test_user_registration():
    unique_email = f"test_{uuid.uuid4()}@example.com"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "securepassword123",
        },
    )

    try:
        assert response.status_code == 200
        assert response.json()["email"] == unique_email
    finally:
        app.dependency_overrides.clear()
