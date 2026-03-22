from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.inference_job import InferenceJob
from app.models.user import User
from app.services.dispatcher import InferenceDispatcher
from app.services.model_registry import ModelRegistryService


class InferenceJobService:
    def __init__(
        self,
        model_registry: ModelRegistryService | None = None,
        dispatcher: InferenceDispatcher | None = None,
    ) -> None:
        self._model_registry = model_registry or ModelRegistryService()
        self._dispatcher = dispatcher or InferenceDispatcher()

    def create_queued_job(
        self,
        db: Session,
        user: User,
        model_id: str,
        original_filename: str,
        file_bytes: bytes,
    ) -> InferenceJob:
        model = self._validate_model(model_id)
        saved_path = self._store_upload(original_filename, file_bytes)
        job = InferenceJob(
            id=str(uuid4()),
            user_id=user.id,
            engine_id=model.engine_id,
            model_id=model.model_id,
            status="queued",
            input_path=str(saved_path),
            original_filename=Path(original_filename).name,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        self._dispatcher.dispatch(job)
        return job

    def get_owned_job(self, db: Session, user: User, job_id: str) -> InferenceJob:
        job = db.query(InferenceJob).filter(InferenceJob.id == job_id, InferenceJob.user_id == user.id).first()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NOT_FOUND",
                    "message": "Inference job was not found.",
                    "details": {"job_id": job_id},
                },
            )
        return job

    def _validate_model(self, model_id: str):
        try:
            return self._model_registry.validate_model_id(model_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_MODEL",
                    "message": str(exc),
                    "details": {"field": "model_id"},
                },
            ) from exc

    def _store_upload(self, original_filename: str, file_bytes: bytes) -> Path:
        settings = get_settings()
        suffix = Path(original_filename).suffix.lower()
        allowed_extensions = {
            extension.strip().lower()
            for extension in settings.allowed_image_extensions.split(",")
            if extension.strip()
        }

        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": "Only supported image file types may be uploaded.",
                    "details": {"field": "image"},
                },
            )

        max_upload_bytes = settings.max_upload_mb * 1024 * 1024
        if len(file_bytes) > max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"Upload exceeds the {settings.max_upload_mb}MB limit.",
                    "details": {"field": "image"},
                },
            )

        job_dir = Path(settings.media_root) / "inference_jobs" / str(uuid4())
        job_dir.mkdir(parents=True, exist_ok=True)
        target_path = job_dir / f"input{suffix}"
        target_path.write_bytes(file_bytes)
        return target_path