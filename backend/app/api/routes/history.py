from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.inference_jobs import InferenceJobService

router = APIRouter()


@router.get("/history")
def get_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    model_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InferenceJobService()
    payload = service.list_history(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        model_id=model_id,
    )
    return success_response(request, payload)


@router.delete("/history/{job_id}")
def delete_history_item(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InferenceJobService()
    service.delete_owned_history_job(db=db, user=current_user, job_id=job_id)
    return success_response(
        request,
        {
            "message": "History item deleted.",
            "job_id": job_id,
        },
    )


@router.delete("/history")
def clear_history(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InferenceJobService()
    deleted_count = service.clear_owned_history(db=db, user=current_user)
    return success_response(
        request,
        {
            "message": "History cleared.",
            "deleted_count": deleted_count,
        },
    )

