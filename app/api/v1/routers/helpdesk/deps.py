from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request


def require_tracker_user(request: Request) -> dict[str, Any]:
    """Пользователь из AuthMiddleware (request.state.user)."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
