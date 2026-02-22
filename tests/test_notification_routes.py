from fastapi.testclient import TestClient

from gateway.dependencies.auth import get_current_user
from gateway.main import app
from shared.database.session import get_db

client = TestClient(app)


def override_get_db():
    yield object()


def override_get_current_user():
    return {"user_id": "user-1", "email": "user@example.com", "token": "token"}


def test_get_preferences_returns_default_when_missing(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    monkeypatch.setattr(
        "gateway.api.v1.notification_routes.get_user_preferences",
        lambda db, user_id: None,
    )
    monkeypatch.setattr(
        "gateway.api.v1.notification_routes.upsert_user_preferences",
        lambda db, user_id, payload: type(
            "Pref",
            (),
            {
                "channel_priority": ["email", "push", "sms"],
                "email_enabled": True,
                "sms_enabled": False,
                "push_enabled": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
            },
        )(),
    )

    response = client.get("/api/v1/notifications/preferences")
    try:
        assert response.status_code == 200
        body = response.json()
        assert body["email_enabled"] is True
        assert body["channel_priority"] == ["email", "push", "sms"]
    finally:
        app.dependency_overrides.clear()


def test_update_preferences(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    monkeypatch.setattr(
        "gateway.api.v1.notification_routes.upsert_user_preferences",
        lambda db, user_id, payload: type(
            "Pref",
            (),
            {
                "channel_priority": payload.get("channel_priority", ["email"]),
                "email_enabled": payload.get("email_enabled", True),
                "sms_enabled": payload.get("sms_enabled", False),
                "push_enabled": payload.get("push_enabled", True),
                "quiet_hours_start": payload.get("quiet_hours_start"),
                "quiet_hours_end": payload.get("quiet_hours_end"),
            },
        )(),
    )

    response = client.post(
        "/api/v1/notifications/preferences",
        json={
            "channel_priority": ["sms", "email"],
            "email_enabled": True,
            "sms_enabled": True,
            "push_enabled": False,
        },
    )
    try:
        assert response.status_code == 200
        body = response.json()
        assert body["channel_priority"] == ["sms", "email"]
        assert body["sms_enabled"] is True
        assert body["push_enabled"] is False
    finally:
        app.dependency_overrides.clear()
