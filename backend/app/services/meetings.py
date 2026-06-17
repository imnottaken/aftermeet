from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Meeting


@dataclass
class MeetingCreateResult:
    meeting_id: str
    filename: str
    transcript_status: str


class MeetingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_upload_meeting(self, original_filename: str) -> MeetingCreateResult:
        meeting_id = str(uuid4())
        meeting = Meeting(
            id=meeting_id,
            title=None,
            original_filename=original_filename,
            transcript_status="pending",
        )
        self.db.add(meeting)
        self.db.commit()
        return MeetingCreateResult(
            meeting_id=meeting_id,
            filename=original_filename,
            transcript_status="pending",
        )

