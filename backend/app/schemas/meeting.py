from pydantic import BaseModel, ConfigDict


class UploadMeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    meeting_id: str
    filename: str
    transcript_status: str

