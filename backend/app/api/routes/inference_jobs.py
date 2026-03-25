import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.inference_jobs import InferenceJobService

router = APIRouter()


def _to_number(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_detection(raw_detection: Mapping[str, object]) -> dict[str, object]:
    raw_bbox = raw_detection.get("bbox")
    bbox = raw_bbox if isinstance(raw_bbox, Mapping) else {}

    raw_confidence = raw_detection.get("confidence")
    confidence = None
    if isinstance(raw_confidence, int | float):
        confidence = float(raw_confidence)

    label = raw_detection.get("label")
    return {
        "label": str(label) if label is not None else "unknown",
        "confidence": confidence,
        "bbox": {
            "x1": _to_number(bbox.get("x1")),
            "y1": _to_number(bbox.get("y1")),
            "x2": _to_number(bbox.get("x2")),
            "y2": _to_number(bbox.get("y2")),
        },
    }


def _serialize_utc_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        normalized = value.replace(tzinfo=UTC)
    else:
        normalized = value.astimezone(UTC)

    return normalized.isoformat().replace("+00:00", "Z")


@router.post("/inference/jobs")
async def create_inference_job(
    request: Request,
    background_tasks: BackgroundTasks,
    model_id: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await image.read()
    job_service = InferenceJobService()
    job = job_service.create_queued_job(
        db=db,
        user=current_user,
        model_id=model_id,
        original_filename=image.filename or "upload.jpg",
        file_bytes=file_bytes,
    )
    job_service.dispatch_job(background_tasks=background_tasks, job_id=job.id)

    return success_response(
        request,
        {
            "job_id": job.id,
            "status": job.status,
            "model_id": job.model_id,
            "engine_id": job.engine_id,
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.post("/inference/jobs/{job_id}/cancel")
def cancel_inference_job(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job_service = InferenceJobService()
    job = job_service.cancel_owned_job(db=db, user=current_user, job_id=job_id)

    if job.status == "running":
        message = "Cancellation requested."
    elif job.status == "cancelled":
        message = "Job cancelled."
    else:
        message = "Job is already in a terminal state."

    return success_response(
        request,
        {
            "job_id": job.id,
            "status": job.status,
            "message": message,
        },
    )


@router.get("/inference/jobs/{job_id}")
def get_inference_job(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job_service = InferenceJobService()
    job = job_service.get_owned_job(db=db, user=current_user, job_id=job_id)

    detections: list[dict[str, object]] = []
    if job.detections_json:
        try:
            parsed = json.loads(job.detections_json)
        except json.JSONDecodeError:
            parsed = []
        if isinstance(parsed, list):
            detections = [_normalize_detection(item) for item in parsed if isinstance(item, Mapping)]

    error_payload = None
    if job.error_code or job.error_message:
        error_payload = {
            "code": job.error_code or "ENGINE_EXECUTION_FAILED",
            "message": job.error_message or "Inference job failed.",
            "details": {"job_id": job.id},
        }

    result_payload = None
    if job.status == "succeeded":
        image_refs = [
            {
                "id": f"{job.id}-original",
                "kind": "original",
                "path": job.input_path,
            }
        ]
        if job.output_path:
            image_refs.append(
                {
                    "id": f"{job.id}-annotated",
                    "kind": "annotated",
                    "path": job.output_path,
                }
            )

        result_payload = {
            "model_id": job.model_id,
            "engine_id": job.engine_id,
            "detections": detections,
            "image_refs": image_refs,
            "duration_ms": job.duration_ms or 0,
        }

    return success_response(
        request,
        {
            "job_id": job.id,
            "status": job.status,
            "model_id": job.model_id,
            "engine_id": job.engine_id,
            "created_at": _serialize_utc_timestamp(job.created_at),
            "started_at": _serialize_utc_timestamp(job.started_at),
            "finished_at": _serialize_utc_timestamp(job.finished_at),
            "result": result_payload,
            "error": error_payload,
        },
    )


@router.get("/inference/jobs/{job_id}/image/{kind}")
def get_inference_job_image(
    job_id: str,
    kind: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if kind not in {"original", "annotated"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_IMAGE_KIND",
                "message": "Unsupported image kind. Use 'original' or 'annotated'.",
                "details": {"field": "kind", "value": kind},
            },
        )

    job_service = InferenceJobService()
    job = job_service.get_owned_job(db=db, user=current_user, job_id=job_id)

    image_path_raw = job.input_path if kind == "original" else job.output_path
    if not image_path_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "IMAGE_NOT_FOUND",
                "message": f"Requested {kind} image is not available for this job.",
                "details": {"job_id": job_id, "kind": kind},
            },
        )

    image_path = Path(image_path_raw)
    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "IMAGE_NOT_FOUND",
                "message": f"Requested {kind} image file does not exist.",
                "details": {"job_id": job_id, "kind": kind},
            },
        )

    return FileResponse(path=image_path, filename=image_path.name)
