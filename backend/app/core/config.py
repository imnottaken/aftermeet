from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'aftermeet.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AfterMeet Backend"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(default=DEFAULT_SQLITE_URL, alias="DATABASE_URL")
    api_v1_prefix: str = "/api/v1"
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=100, alias="MAX_UPLOAD_SIZE_MB")
    whisper_model_name: str = Field(default="small", alias="WHISPER_MODEL_NAME")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
