from fastapi.testclient import TestClient
from gateway.main import app
import uuid


client = TestClient(app)


def test_user_registration():

    unique_email = f"test_{uuid.uuid4()}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "securepassword123"
        }
    )

    assert response.status_code == 200
    assert response.json()["email"] == unique_email
