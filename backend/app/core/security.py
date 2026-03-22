from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _build_token(subject: str, role: str, token_type: str, expires_minutes: int, jti: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def create_access_token(user_id: int, role: str) -> tuple[str, str]:
    jti = str(uuid4())
    token = _build_token(
        subject=str(user_id),
        role=role,
        token_type="access",
        expires_minutes=get_settings().jwt_access_expires_minutes,
        jti=jti,
    )
    return token, jti


def create_refresh_token(user_id: int, role: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    jti = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_refresh_expires_minutes)
    token = _build_token(
        subject=str(user_id),
        role=role,
        token_type="refresh",
        expires_minutes=settings.jwt_refresh_expires_minutes,
        jti=jti,
    )
    return token, jti, expires_at


def decode_token(token: str, expected_type: str | None = None) -> dict[str, object]:
    settings = get_settings()
    try:
        payload: dict[str, object] = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Token is invalid or expired") from exc

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise ValueError("Token type is invalid")

    return payload