import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.response import success_response
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest

router = APIRouter()


def _validate_password_strength(password: str) -> None:
    if len(password) < 8 or re.search(r"[A-Za-z]", password) is None or re.search(r"\d", password) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Password must be at least 8 characters and include at least one letter and one number.",
                "details": {"field": "password"},
            },
        )


def _build_auth_payload(user: User, access_token: str, refresh_token: str) -> dict[str, object]:
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": get_settings().jwt_access_expires_minutes * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
    }


def _issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token, _ = create_access_token(user.id, user.role)
    refresh_token, refresh_jti, expires_at = create_refresh_token(user.id, user.role)

    db.add(
        RefreshToken(
            user_id=user.id,
            jti=refresh_jti,
            expires_at=expires_at,
        )
    )
    db.commit()

    return access_token, refresh_token


@router.post("/register")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    _validate_password_strength(payload.password)

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AUTH_EMAIL_EXISTS",
                "message": "An account with this email already exists.",
                "details": {"field": "email"},
            },
        )

    user = User(email=email, password_hash=hash_password(payload.password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token, refresh_token = _issue_tokens(db, user)
    return success_response(request, _build_auth_payload(user, access_token, refresh_token), status_code=status.HTTP_201_CREATED)


@router.post("/login")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "details": {},
            },
        )

    access_token, refresh_token = _issue_tokens(db, user)
    return success_response(request, _build_auth_payload(user, access_token, refresh_token))


@router.post("/refresh")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_TOKEN_INVALID",
                "message": str(exc),
                "details": {},
            },
        ) from exc

    jti = str(decoded.get("jti", ""))

    try:
        user_id = int(decoded.get("sub", 0))
    except (TypeError, ValueError):
        user_id = 0

    if not jti or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "Token payload is malformed.", "details": {}},
        )

    token_record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_record is None or token_record.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "Refresh token is not active.", "details": {}},
        )

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_EXPIRED", "message": "Refresh token has expired.", "details": {}},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "User not found for token.", "details": {}},
        )

    access_token, _ = create_access_token(user.id, user.role)

    return success_response(
        request,
        _build_auth_payload(user, access_token, payload.refresh_token),
    )


@router.post("/logout")
def logout(request: Request, payload: LogoutRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except ValueError:
        return success_response(request, {"message": "Logged out."})

    jti = str(decoded.get("jti", ""))
    if jti:
        token_record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if token_record and not token_record.is_revoked:
            token_record.is_revoked = True
            token_record.revoked_at = datetime.now(UTC)
            db.add(token_record)
            db.commit()

    return success_response(request, {"message": "Logged out."})