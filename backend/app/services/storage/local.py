from pathlib import Path

from fastapi import UploadFile


class LocalUploadStorage:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)

    def save(self, meeting_id: str, original_filename: str, file: UploadFile) -> Path:
        destination = self.base_dir / meeting_id / original_filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        file.file.seek(0)
        with destination.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)
        file.file.seek(0)
        return destination

