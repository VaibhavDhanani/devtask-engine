from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

TokenType = Literal["access", "refresh"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(subject: UUID, token_type: TokenType) -> str:
    if token_type == "access":
        expires = _now() + timedelta(minutes=settings.jwt_access_token_ttl_minutes)
    else:
        expires = _now() + timedelta(days=settings.jwt_refresh_token_ttl_days)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(_now().timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, *, expected_type: TokenType) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError("Wrong token type")

    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise UnauthorizedError("Invalid token subject")

    try:
        return UUID(sub)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token subject") from exc
