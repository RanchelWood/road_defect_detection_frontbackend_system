from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    jwt_secret_key: str = "replace_me_with_secure_value"
    jwt_access_expires_minutes: int = 60
    jwt_refresh_expires_minutes: int = 10080

    database_url: str = "sqlite:///./data/app.db"
    media_root: str = "./media"

    max_upload_mb: int = 10
    allowed_image_extensions: str = ".jpg,.jpeg,.png"
    yolo_device: str = "cpu"

    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()