from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.inference_jobs import InferenceJobService

router = APIRouter()


@router.post("/inference/jobs")
async def create_inference_job(
    request: Request,
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


@router.get("/inference/jobs/{job_id}")
def get_inference_job(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job_service = InferenceJobService()
    job = job_service.get_owned_job(db=db, user=current_user, job_id=job_id)

    error_payload = None
    if job.error_code or job.error_message:
        error_payload = {
            "code": job.error_code or "ENGINE_EXECUTION_FAILED",
            "message": job.error_message or "Inference job failed.",
            "details": {"job_id": job.id},
        }

    return success_response(
        request,
        {
            "job_id": job.id,
            "status": job.status,
            "model_id": job.model_id,
            "engine_id": job.engine_id,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "result": None,
            "error": error_payload,
        },
    )