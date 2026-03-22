from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse


def build_meta(request: Request) -> dict[str, str]:
    request_id = getattr(request.state, "request_id", "")
    return {
        "request_id": request_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def success_response(request: Request, data: dict[str, object], status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "meta": build_meta(request),
        },
    )


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "meta": build_meta(request),
        },
    )