from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, inference_jobs, models
from app.core.config import get_settings
from app.core.database import init_db
from app.core.response import error_response
from app.services.inference_jobs import InferenceJobService


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Road Damage Defect System API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            return error_response(
                request,
                status_code=exc.status_code,
                code=str(exc.detail.get("code", "HTTP_ERROR")),
                message=str(exc.detail.get("message", "Request failed.")),
                details=exc.detail.get("details", {}),
            )

        return error_response(
            request,
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            details={"reason": str(exc)},
        )

    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(models.router, tags=["models"])
    app.include_router(inference_jobs.router, tags=["inference"])

    @app.on_event("startup")
    def on_startup() -> None:
        Path(settings.media_root).mkdir(parents=True, exist_ok=True)
        init_db()
        InferenceJobService().recover_pending_jobs_on_startup()

    return app


app = create_app()