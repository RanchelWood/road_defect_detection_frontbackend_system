from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.response import success_response
from app.models.user import User
from app.services.model_registry import ModelRegistryService

router = APIRouter()


@router.get("/models")
def list_models(request: Request, current_user: User = Depends(get_current_user)):
    _ = current_user
    model_registry = ModelRegistryService()
    items = [
        {
            "model_id": model.model_id,
            "engine_id": model.engine_id,
            "status": model.status,
            "performance_notes": model.performance_notes,
            "display_name": model.display_name,
            "description": model.description,
            "runtime_type": model.runtime_type,
        }
        for model in model_registry.list_models()
    ]
    return success_response(request, {"items": items})