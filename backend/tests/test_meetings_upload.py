from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session import get_db
from app.main import create_app
from app.api.v1.meetings import get_storage
from app.core.config import get_settings


@pytest.fixture()
def client(tmp_path):
    db_url = "sqlite:///./test_aftermeet.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    class TestStorage:
        def __init__(self, base_dir: str) -> None:
            self.base_dir = Path(tmp_path / "uploads")

        def save(self, meeting_id: str, original_filename: str, file):
            destination = self.base_dir / meeting_id / original_filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(file.file.read())
            file.file.seek(0)
            return destination

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: TestStorage("uploads")
    app.dependency_overrides[get_settings] = lambda: get_settings()

    return TestClient(app)


def test_upload_meeting_audio_success(client):
    response = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meeting_id"]
    assert body["filename"] == "sample.mp3"
    assert body["transcript_status"] == "pending"


def test_upload_meeting_audio_rejects_invalid_extension(client):
    response = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_meeting_audio_rejects_oversized_file(client):
    oversized = b"0" * (101 * 1024 * 1024)
    response = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("sample.wav", oversized, "audio/wav")},
    )
    assert response.status_code == 413
