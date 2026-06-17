from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AfterMeet Backend"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = "/api/v1"
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=100, alias="MAX_UPLOAD_SIZE_MB")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
