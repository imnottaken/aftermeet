from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.meeting import UploadMeetingResponse
from app.services.meetings import MeetingService
from app.services.storage.local import LocalUploadStorage

router = APIRouter(prefix="/api/v1/meetings", tags=["meetings"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}


def get_meeting_service(db: Session = Depends(get_db)) -> MeetingService:
    return MeetingService(db)


def get_storage(settings: Settings = Depends(get_settings)) -> LocalUploadStorage:
    return LocalUploadStorage(settings.upload_dir)


def validate_upload(file: UploadFile, max_upload_size_mb: int) -> None:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed types: .mp3, .wav, .m4a",
        )

    max_bytes = max_upload_size_mb * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum size of 100 MB",
        )


@router.post("/upload", response_model=UploadMeetingResponse)
def upload_meeting_audio(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    meeting_service: MeetingService = Depends(get_meeting_service),
    storage: LocalUploadStorage = Depends(get_storage),
) -> UploadMeetingResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )

    validate_upload(file, settings.max_upload_size_mb)
    result = meeting_service.create_upload_meeting(file.filename)
    storage.save(result.meeting_id, file.filename, file)
    return UploadMeetingResponse(**result.__dict__)

