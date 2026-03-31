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

    inference_autorun_enabled: bool = True
    rddc2020_python_path: str = r"D:\anaconda3\envs\crddc2022\python.exe"
    rddc2020_yolov5_root: str = r"D:\road_defect_detection\rddc2020\yolov5"
    rddc2020_device: str = "cpu"
    rddc2020_timeout_seconds: int = 180

    orddc2024_python_path: str = r"D:\anaconda3\envs\orddc2024\python.exe"
    orddc2024_root: str = r"D:\road_defect_detection\orddc2024-main"
    orddc2024_timeout_seconds: int = 180
    shiyu_grddc2022_python_path: str = r"D:\anaconda3\envs\crddc2022\python.exe"
    shiyu_grddc2022_root: str = r"D:\road_defect_detection\ShiYu_SeaView_GRDDC2022"
    shiyu_grddc2022_device: str = "cpu"
    shiyu_grddc2022_timeout_seconds_single: int = 180
    shiyu_grddc2022_timeout_seconds_ensemble: int = 360
    shiyu_grddc2022_timeout_seconds_mmdet: int = 360
    shiyu_grddc2022_mmdet_config: str = r"configs\\swin\\faster_swin_l.py"
    shiyu_grddc2022_mmdet_checkpoint: str = "Faster_Swin_l_w7_ms_1and2.pth"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

