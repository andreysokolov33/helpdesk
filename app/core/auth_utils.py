# app/core/auth_utils.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError

from app.config import settings

logger = logging.getLogger("abs")


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
