# app/core/auth_utils.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError

from app.config import settings

logger = logging.getLogger("abs")

_COOKIE_BASE = {"path": "/", "httponly": True, "samesite": "lax"}


def _resolve_cookie_secure(*, scheme: str | None, forwarded_proto: str | None) -> bool:
    if settings.MODE == "DEV":
        return False
    if settings.PROXY_HEADERS and forwarded_proto:
        return forwarded_proto.split(",")[0].strip().lower() == "https"
    return (scheme or "http").lower() == "https"


def auth_cookie_options(request) -> dict:
    """Параметры Set-Cookie: Secure только за HTTPS (или DEV без Secure)."""
    forwarded = request.headers.get("x-forwarded-proto") if settings.PROXY_HEADERS else None
    secure = _resolve_cookie_secure(scheme=request.url.scheme, forwarded_proto=forwarded)
    return {**_COOKIE_BASE, "secure": secure}


def auth_cookie_options_from_scope(scope: dict) -> dict:
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    forwarded = headers.get("x-forwarded-proto") if settings.PROXY_HEADERS else None
    secure = _resolve_cookie_secure(scheme=scope.get("scheme"), forwarded_proto=forwarded)
    return {**_COOKIE_BASE, "secure": secure}


async def create_token(user: dict, token_type: str = "access") -> tuple[str, datetime, str]:
    user_id = user["id"]
    role = user.get("role", "user")
    admin = user.get("is_superuser", False)
    now = datetime.now(timezone.utc)

    if token_type == "access":
        expire = now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
        secret = settings.SECRET_KEY
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        secret = settings.REFRESH_SECRET_KEY

    jti = str(uuid4())
    payload = {
        "iat": now,
        "exp": expire,
        "jti": jti,
        "user_id": user_id,
        "type": token_type,
    }
    if token_type == "access":
        payload["role"] = role
        payload["admin"] = admin

    token = jwt.encode(payload, secret, algorithm=settings.ALGORITHM)
    return token, expire, jti


async def decode_jwt_token(token: str, token_type: str = "access") -> dict | None:
    if not token:
        return None
    secret = settings.SECRET_KEY if token_type == "access" else settings.REFRESH_SECRET_KEY
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except (InvalidTokenError, PyJWTError) as e:
        logger.debug("JWT decode error (%s): %s", token_type, e)
        return None
