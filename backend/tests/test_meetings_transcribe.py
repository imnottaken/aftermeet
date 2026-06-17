from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.meetings import get_storage, get_transcription_service
from app.core.config import Settings, get_settings
from app.db.models import Base, Meeting, Transcript
from app.db.session import get_db
from app.main import create_app
from app.services.transcription import TranscriptionResult, TranscriptionService


class FakeTranscriber:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        if self.should_fail:
            raise RuntimeError("transcription crashed")
        return TranscriptionResult(
            transcript_text="hello world",
            language_detected="en",
            duration_seconds=42,
        )


@pytest.fixture()
def transcribe_app(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    settings = Settings(
        APP_ENV="test",
        DATABASE_URL=db_url,
        UPLOAD_DIR=str(tmp_path / "uploads"),
        WHISPER_MODEL_NAME="small",
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_settings():
        return settings

    def build_service(should_fail: bool = False):
        db = TestingSessionLocal()
        return TranscriptionService(
            db=db,
            settings=settings,
            storage_dir=settings.upload_dir,
            transcriber=FakeTranscriber(should_fail=should_fail),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_storage] = lambda: None

    def seed_meeting(meeting_id: str = "meeting-1", filename: str = "sample.mp3"):
        with TestingSessionLocal() as db:
            db.add(
                Meeting(
                    id=meeting_id,
                    title=None,
                    original_filename=filename,
                    transcript_status="pending",
                )
            )
            db.commit()
        audio_path = Path(settings.upload_dir) / meeting_id / filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"fake-audio")
        return audio_path

    return app, TestingSessionLocal, build_service, seed_meeting


def test_transcribe_meeting_success(transcribe_app):
    app, TestingSessionLocal, build_service, seed_meeting = transcribe_app
    seed_meeting()
    app.dependency_overrides[get_transcription_service] = lambda: build_service()

    client = TestClient(app)
    response = client.post("/api/v1/meetings/meeting-1/transcribe")

    assert response.status_code == 200
    assert response.json() == {
        "meeting_id": "meeting-1",
        "transcript_status": "completed",
        "language_detected": "en",
        "duration_seconds": 42,
    }

    with TestingSessionLocal() as db:
        meeting = db.query(Meeting).filter(Meeting.id == "meeting-1").one()
        transcript = db.query(Transcript).filter(Transcript.meeting_id == "meeting-1").one()
        assert meeting.transcript_status == "completed"
        assert transcript.transcript_text == "hello world"
        assert transcript.language_detected == "en"
        assert transcript.duration_seconds == 42


def test_transcribe_meeting_returns_404_for_missing_meeting(transcribe_app):
    app, _, build_service, _ = transcribe_app
    app.dependency_overrides[get_transcription_service] = lambda: build_service()

    client = TestClient(app)
    response = client.post("/api/v1/meetings/missing/transcribe")

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_transcribe_meeting_marks_failed_on_transcriber_error(transcribe_app):
    app, TestingSessionLocal, build_service, seed_meeting = transcribe_app
    seed_meeting()
    app.dependency_overrides[get_transcription_service] = lambda: build_service(
        should_fail=True
    )

    client = TestClient(app)
    response = client.post("/api/v1/meetings/meeting-1/transcribe")

    assert response.status_code == 500
    assert response.json()["detail"] == "Transcription failed"

    with TestingSessionLocal() as db:
        meeting = db.query(Meeting).filter(Meeting.id == "meeting-1").one()
        assert meeting.transcript_status == "failed"
