from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Meeting, Transcript

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    transcript_text: str
    language_detected: str | None
    duration_seconds: int | None
    transcript_status: str = "completed"


class WhisperTranscriber:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self.model_name)
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        model = self._load_model()
        segments, info = model.transcribe(str(audio_path))
        transcript_text = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        ).strip()
        duration_seconds = None
        if getattr(info, "duration", None) is not None:
            duration_seconds = int(info.duration)
        return TranscriptionResult(
            transcript_text=transcript_text,
            language_detected=getattr(info, "language", None),
            duration_seconds=duration_seconds,
        )


@lru_cache(maxsize=1)
def get_whisper_transcriber(model_name: str) -> WhisperTranscriber:
    return WhisperTranscriber(model_name)


class TranscriptionService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        storage_dir: str,
        transcriber: WhisperTranscriber | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.storage_dir = Path(storage_dir)
        self.transcriber = transcriber or get_whisper_transcriber(
            settings.whisper_model_name
        )

    def _get_meeting(self, meeting_id: str) -> Meeting:
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).one_or_none()
        if meeting is None:
            raise ValueError("Meeting not found")
        return meeting

    def _meeting_audio_path(self, meeting: Meeting) -> Path:
        return self.storage_dir / meeting.id / meeting.original_filename

    def transcribe_meeting(self, meeting_id: str) -> TranscriptionResult:
        meeting = self._get_meeting(meeting_id)
        audio_path = self._meeting_audio_path(meeting)
        if not audio_path.exists():
            raise FileNotFoundError("Audio file not found")

        logger.info("Starting transcription", extra={"meeting_id": meeting_id})
        meeting.transcript_status = "processing"
        self.db.commit()

        try:
            result = self.transcriber.transcribe(audio_path)
            transcript = Transcript(
                id=str(uuid4()),
                meeting_id=meeting.id,
                transcript_text=result.transcript_text,
                language_detected=result.language_detected,
                duration_seconds=result.duration_seconds,
            )
            self.db.add(transcript)
            meeting.transcript_status = "completed"
            self.db.commit()
            logger.info("Transcription completed", extra={"meeting_id": meeting_id})
            return TranscriptionResult(
                transcript_text=result.transcript_text,
                language_detected=result.language_detected,
                duration_seconds=result.duration_seconds,
                transcript_status="completed",
            )
        except Exception:
            self.db.rollback()
            meeting = self._get_meeting(meeting_id)
            meeting.transcript_status = "failed"
            self.db.commit()
            logger.exception("Transcription failed", extra={"meeting_id": meeting_id})
            raise
