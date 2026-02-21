import io
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from gateway.api.v1.document_routes import get_document_service
from gateway.dependencies.auth import get_current_user
from gateway.main import app
from shared.database.session import get_db

client = TestClient(app)


class FakeDocumentService:
    def upload_document(self, db, file, user_id):
        return SimpleNamespace(
            id=uuid.uuid4(),
            file_name=file.filename,
            file_type=file.content_type,
            document_status="uploaded",
            uploaded_at=datetime.now(timezone.utc),
        )


class FakeInvalidDocumentService:
    def upload_document(self, db, file, user_id):
        raise ValueError("Unsupported content type: application/x-msdownload")


def override_get_db():
    yield object()


def override_get_current_user():
    return {"user_id": uuid.uuid4()}


def test_document_upload():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()

    file_data = io.BytesIO(b"dummy content")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
    )

    try:
        assert response.status_code == 200
        assert response.json()["file_name"] == "test.pdf"
    finally:
        app.dependency_overrides.clear()


def test_document_upload_invalid_file():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_document_service] = lambda: FakeInvalidDocumentService()

    file_data = io.BytesIO(b"dummy content")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.exe", file_data, "application/x-msdownload")},
    )

    try:
        assert response.status_code == 400
        assert "Unsupported content type" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
