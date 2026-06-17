from pydantic import BaseModel, ConfigDict


class TranscribeMeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    meeting_id: str
    transcript_status: str
    language_detected: str | None = None
    duration_seconds: int | None = None

