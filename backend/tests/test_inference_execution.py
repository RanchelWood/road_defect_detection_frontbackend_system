import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.security import hash_password
from app.models.inference_job import InferenceJob
from app.models.user import User
from app.services.adapters.base import (
    AdapterExecutionError,
    AdapterExecutionResult,
    InferenceEngineAdapter,
    ModelPreset,
)
from app.services.dispatcher import InferenceDispatcher
from app.services.inference_jobs import InferenceJobService
from app.services.model_registry import ModelRegistryService

VALID_IMAGE_BYTES = bytes.fromhex("89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000A49444154789C6360000000020001E527D4A20000000049454E44AE426082")


class StaticEngineRegistry:
    def __init__(self, adapter: InferenceEngineAdapter) -> None:
        self._adapter = adapter

    def list_adapters(self) -> list[InferenceEngineAdapter]:
        return [self._adapter]

    def get_adapter(self, engine_id: str) -> InferenceEngineAdapter | None:
        if engine_id == self._adapter.engine_id:
            return self._adapter
        return None


class SuccessfulAdapter(InferenceEngineAdapter):
    @property
    def engine_id(self) -> str:
        return "fake-engine"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="fake-model",
                engine_id=self.engine_id,
                display_name="Fake Model",
                description="Test-only successful adapter model.",
            )
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        _ = (model, cancel_requested)
        assert Path(input_image_path).exists()
        workspace = Path(job_workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        output = workspace / "annotated.jpg"
        output.write_bytes(b"annotated-image")
        return AdapterExecutionResult(
            annotated_image_path=str(output),
            detections=[{"label": "D00", "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4}}],
            duration_ms=123,
        )


class FailingAdapter(InferenceEngineAdapter):
    @property
    def engine_id(self) -> str:
        return "fake-engine"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="fake-model",
                engine_id=self.engine_id,
                display_name="Fake Model",
                description="Test-only failing adapter model.",
            )
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        _ = (input_image_path, job_workspace, model, cancel_requested)
        raise AdapterExecutionError("ENGINE_RUNTIME_ERROR", "Simulated adapter runtime failure")


class CancelledAdapter(InferenceEngineAdapter):
    @property
    def engine_id(self) -> str:
        return "fake-engine"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="fake-model",
                engine_id=self.engine_id,
                display_name="Fake Model",
                description="Test-only cancelled adapter model.",
            )
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        _ = (input_image_path, job_workspace, model, cancel_requested)
        raise AdapterExecutionError("JOB_CANCELLED", "Inference job was cancelled.")


class CountingAdapter(InferenceEngineAdapter):
    def __init__(self) -> None:
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self._lock = threading.Lock()

    @property
    def engine_id(self) -> str:
        return "fake-engine"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="fake-model",
                engine_id=self.engine_id,
                display_name="Fake Model",
                description="Test-only counting adapter model.",
            )
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        _ = (input_image_path, model, cancel_requested)
        with self._lock:
            self.calls += 1

        self.started.set()
        self.release.wait(timeout=5)

        workspace = Path(job_workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        output = workspace / "annotated.jpg"
        output.write_bytes(b"annotated-image")
        return AdapterExecutionResult(
            annotated_image_path=str(output),
            detections=[{"label": "D00", "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4}}],
            duration_ms=77,
        )


def _create_user(db_session):
    user = User(
        email=f"exec-{uuid4()}@example.com",
        password_hash=hash_password("Password1"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_execute_job_marks_succeeded_and_persists_results(db_session):
    adapter = SuccessfulAdapter()
    registry = StaticEngineRegistry(adapter)
    service = InferenceJobService(
        model_registry=ModelRegistryService(engine_registry=registry),
        engine_registry=registry,
        dispatcher=InferenceDispatcher(autorun_enabled=False),
    )

    user = _create_user(db_session)
    job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="road.png",
        file_bytes=VALID_IMAGE_BYTES,
    )

    assert job.status == "queued"

    service.execute_job(job.id)
    db_session.expire_all()

    refreshed = db_session.query(InferenceJob).filter(InferenceJob.id == job.id).first()
    assert refreshed is not None
    assert refreshed.status == "succeeded"
    assert refreshed.started_at is not None
    assert refreshed.finished_at is not None
    assert refreshed.output_path is not None
    assert refreshed.detections_json is not None
    assert refreshed.duration_ms == 123
    assert refreshed.error_code is None
    assert refreshed.error_message is None


def test_execute_job_marks_failed_on_adapter_error(db_session, caplog):
    adapter = FailingAdapter()
    registry = StaticEngineRegistry(adapter)
    service = InferenceJobService(
        model_registry=ModelRegistryService(engine_registry=registry),
        engine_registry=registry,
        dispatcher=InferenceDispatcher(autorun_enabled=False),
    )

    user = _create_user(db_session)
    job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="road.png",
        file_bytes=VALID_IMAGE_BYTES,
    )

    with caplog.at_level(logging.INFO, logger="app.services.inference_jobs"):
        service.execute_job(job.id)
    db_session.expire_all()

    refreshed = db_session.query(InferenceJob).filter(InferenceJob.id == job.id).first()
    assert refreshed is not None
    assert refreshed.status == "failed"
    assert refreshed.started_at is not None
    assert refreshed.finished_at is not None
    assert refreshed.error_code == "ENGINE_RUNTIME_ERROR"
    assert "Simulated adapter runtime failure" in (refreshed.error_message or "")

    assert any(
        record.message == "inference_job_failed"
        and getattr(record, "job_id", None) == job.id
        and getattr(record, "error_code", None) == "ENGINE_RUNTIME_ERROR"
        for record in caplog.records
    )


def test_execute_job_marks_cancelled_when_adapter_signals_cancellation(db_session):
    adapter = CancelledAdapter()
    registry = StaticEngineRegistry(adapter)
    service = InferenceJobService(
        model_registry=ModelRegistryService(engine_registry=registry),
        engine_registry=registry,
        dispatcher=InferenceDispatcher(autorun_enabled=False),
    )

    user = _create_user(db_session)
    job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="road.png",
        file_bytes=VALID_IMAGE_BYTES,
    )

    service.execute_job(job.id)
    db_session.expire_all()

    refreshed = db_session.query(InferenceJob).filter(InferenceJob.id == job.id).first()
    assert refreshed is not None
    assert refreshed.status == "cancelled"
    assert refreshed.finished_at is not None
    assert refreshed.error_code == "JOB_CANCELLED"


def test_execute_job_atomic_claim_prevents_duplicate_adapter_run(db_session):
    adapter = CountingAdapter()
    registry = StaticEngineRegistry(adapter)
    service = InferenceJobService(
        model_registry=ModelRegistryService(engine_registry=registry),
        engine_registry=registry,
        dispatcher=InferenceDispatcher(autorun_enabled=False),
    )

    user = _create_user(db_session)
    job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="road.png",
        file_bytes=VALID_IMAGE_BYTES,
    )

    worker = threading.Thread(target=service.execute_job, args=(job.id,))
    worker.start()

    assert adapter.started.wait(timeout=5)

    service.execute_job(job.id)

    adapter.release.set()
    worker.join(timeout=5)
    assert not worker.is_alive()

    db_session.expire_all()
    refreshed = db_session.query(InferenceJob).filter(InferenceJob.id == job.id).first()
    assert refreshed is not None
    assert refreshed.status == "succeeded"
    assert adapter.calls == 1


def test_recover_pending_jobs_requeues_running_jobs(db_session):
    adapter = SuccessfulAdapter()
    registry = StaticEngineRegistry(adapter)
    service = InferenceJobService(
        model_registry=ModelRegistryService(engine_registry=registry),
        engine_registry=registry,
        dispatcher=InferenceDispatcher(autorun_enabled=False),
    )

    user = _create_user(db_session)
    queued_job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="queued.png",
        file_bytes=VALID_IMAGE_BYTES,
    )
    running_job = service.create_queued_job(
        db=db_session,
        user=user,
        model_id="fake-model",
        original_filename="running.png",
        file_bytes=VALID_IMAGE_BYTES,
    )
    running_job.status = "running"
    running_job.started_at = datetime.now(UTC)
    running_job.finished_at = datetime.now(UTC)
    db_session.add(running_job)
    db_session.commit()

    service.recover_pending_jobs_on_startup()
    db_session.expire_all()

    refreshed_queued = db_session.query(InferenceJob).filter(InferenceJob.id == queued_job.id).first()
    refreshed_running = db_session.query(InferenceJob).filter(InferenceJob.id == running_job.id).first()

    assert refreshed_queued is not None
    assert refreshed_queued.status == "queued"
    assert refreshed_queued.error_code is None

    assert refreshed_running is not None
    assert refreshed_running.status == "queued"
    assert refreshed_running.error_code == "ENGINE_RECOVERED_RETRY"
    assert refreshed_running.error_message is not None
    assert refreshed_running.started_at is None
    assert refreshed_running.finished_at is None

