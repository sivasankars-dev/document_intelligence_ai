import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient

from gateway.dependencies.auth import get_current_user
from gateway.main import app
from services.auth_service.auth_service import get_auth_service
from shared.database.session import get_db

client = TestClient(app)


class FakeAuthService:
    def __init__(self):
        self.revoked = set()

    def authenticate_user(self, db, email: str, password: str):
        if email == "user@example.com" and password == "secret123":
            return SimpleNamespace(
                id=uuid.uuid4(),
                email=email,
                is_active=True,
            )
        return None

    def create_access_token(self, user):
        return "valid.jwt.token", 3600

    def revoke_token(self, token: str):
        self.revoked.add(token)


def override_get_db():
    yield object()


def test_login_success():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "secret123"},
    )

    try:
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "valid.jwt.token"
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == 3600
    finally:
        app.dependency_overrides.clear()


def test_login_invalid_credentials():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    try:
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"
    finally:
        app.dependency_overrides.clear()


def test_logout_success():
    fake_service = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": uuid.uuid4(),
        "email": "user@example.com",
        "token": "valid.jwt.token",
    }

    response = client.post("/api/v1/auth/logout")

    try:
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
        assert "valid.jwt.token" in fake_service.revoked
    finally:
        app.dependency_overrides.clear()
