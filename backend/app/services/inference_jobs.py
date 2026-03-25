import json
import math
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.inference_job import InferenceJob
from app.models.user import User
from app.services.adapters.base import AdapterExecutionError
from app.services.dispatcher import InferenceDispatcher
from app.services.engine_registry import InferenceEngineRegistry, get_engine_registry
from app.services.model_registry import ModelRegistryService


class InferenceJobService:
    def __init__(
        self,
        model_registry: ModelRegistryService | None = None,
        engine_registry: InferenceEngineRegistry | None = None,
        dispatcher: InferenceDispatcher | None = None,
    ) -> None:
        self._settings = get_settings()
        self._engine_registry = engine_registry or get_engine_registry()
        self._model_registry = model_registry or ModelRegistryService(engine_registry=self._engine_registry)
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
        return job

    def dispatch_job(self, background_tasks: BackgroundTasks, job_id: str) -> None:
        self._dispatcher.dispatch(background_tasks=background_tasks, job_id=job_id, execute_fn=self.execute_job)

    def recover_pending_jobs_on_startup(self) -> None:
        db = SessionLocal()
        try:
            pending_jobs = (
                db.query(InferenceJob)
                .filter(InferenceJob.status.in_(["queued", "running"]))
                .order_by(InferenceJob.created_at.asc())
                .all()
            )

            if not pending_jobs:
                return

            pending_ids: list[str] = []
            for job in pending_jobs:
                if job.status == "running":
                    job.status = "queued"
                    job.error_code = "ENGINE_RECOVERED_RETRY"
                    job.error_message = "Recovered after server restart and requeued for execution."
                    job.started_at = None
                    job.finished_at = None
                    db.add(job)
                pending_ids.append(job.id)

            db.commit()

            if not self._settings.inference_autorun_enabled:
                return

            for job_id in pending_ids:
                self.execute_job(job_id)
        finally:
            db.close()

    def execute_job(self, job_id: str) -> None:
        db = SessionLocal()
        try:
            job = db.query(InferenceJob).filter(InferenceJob.id == job_id).first()
            if job is None:
                return
            if job.status != "queued":
                return

            job.status = "running"
            job.started_at = datetime.now(UTC)
            job.error_code = None
            job.error_message = None
            db.add(job)
            db.commit()

            try:
                model = self._model_registry.validate_model_id(job.model_id)
            except ValueError as exc:
                raise AdapterExecutionError("INVALID_MODEL", str(exc)) from exc

            adapter = self._engine_registry.get_adapter(job.engine_id)
            if adapter is None:
                raise AdapterExecutionError(
                    "ENGINE_NOT_AVAILABLE",
                    f"Engine '{job.engine_id}' is not registered.",
                )

            workspace = Path(job.input_path).parent / "runtime"
            result = adapter.run(
                input_image_path=job.input_path,
                job_workspace=str(workspace),
                model=model,
            )

            job.status = "succeeded"
            job.output_path = result.annotated_image_path
            job.detections_json = json.dumps(result.detections)
            job.duration_ms = result.duration_ms
            job.finished_at = datetime.now(UTC)
            db.add(job)
            db.commit()
        except AdapterExecutionError as exc:
            self._mark_failed(db=db, job_id=job_id, error_code=exc.code, error_message=exc.message)
        except Exception as exc:  # pragma: no cover - defensive fallback for unexpected runtime issues.
            self._mark_failed(
                db=db,
                job_id=job_id,
                error_code="ENGINE_EXECUTION_FAILED",
                error_message=str(exc),
            )
        finally:
            db.close()

    def _mark_failed(self, db: Session, job_id: str, error_code: str, error_message: str) -> None:
        job = db.query(InferenceJob).filter(InferenceJob.id == job_id).first()
        if job is None:
            return

        job.status = "failed"
        job.error_code = error_code
        job.error_message = error_message[:2000]
        job.finished_at = datetime.now(UTC)
        db.add(job)
        db.commit()

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

    def delete_owned_history_job(self, db: Session, user: User, job_id: str) -> None:
        job = self.get_owned_job(db=db, user=user, job_id=job_id)
        db.delete(job)
        db.commit()

    def clear_owned_history(self, db: Session, user: User) -> int:
        deleted_count = db.query(InferenceJob).filter(InferenceJob.user_id == user.id).delete(synchronize_session=False)
        db.commit()
        return deleted_count

    def list_history(
        self,
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
        model_id: str | None = None,
    ) -> dict[str, object]:
        query = db.query(InferenceJob).filter(InferenceJob.user_id == user.id)
        if model_id:
            query = query.filter(InferenceJob.model_id == model_id)

        total = query.count()
        jobs = (
            query.order_by(InferenceJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [self._build_history_item(job) for job in jobs]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def _build_history_item(self, job: InferenceJob) -> dict[str, object]:
        timestamp = job.finished_at or job.started_at or job.created_at
        item: dict[str, object] = {
            "job_id": job.id,
            "model_id": job.model_id,
            "engine_id": job.engine_id,
            "status": job.status,
            "timestamp": timestamp.isoformat(),
        }

        defect_count, max_confidence = self._extract_detection_stats(job.detections_json)
        if defect_count is not None:
            item["defect_count"] = defect_count
        if max_confidence is not None:
            item["max_confidence"] = max_confidence

        return item

    def _extract_detection_stats(self, detections_json: str | None) -> tuple[int | None, float | None]:
        if not detections_json:
            return None, None

        try:
            parsed = json.loads(detections_json)
        except json.JSONDecodeError:
            return None, None

        if not isinstance(parsed, list):
            return None, None

        defect_count = 0
        confidences: list[float] = []

        for item in parsed:
            if not isinstance(item, dict):
                continue
            defect_count += 1

            confidence = item.get("confidence")
            if confidence is None:
                continue

            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                continue

            if not math.isfinite(confidence_value):
                continue
            if confidence_value < 0 or confidence_value > 1:
                continue

            confidences.append(confidence_value)

        max_confidence = max(confidences) if confidences else None
        return defect_count, max_confidence

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
        suffix = Path(original_filename).suffix.lower()
        allowed_extensions = {
            extension.strip().lower()
            for extension in self._settings.allowed_image_extensions.split(",")
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

        max_upload_bytes = self._settings.max_upload_mb * 1024 * 1024
        if len(file_bytes) > max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"Upload exceeds the {self._settings.max_upload_mb}MB limit.",
                    "details": {"field": "image"},
                },
            )

        job_dir = Path(self._settings.media_root) / "inference_jobs" / str(uuid4())
        job_dir.mkdir(parents=True, exist_ok=True)
        target_path = job_dir / f"input{suffix}"
        target_path.write_bytes(file_bytes)
        return target_path

