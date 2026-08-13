"""Фоновое логирование действий операторов в users.skystream_users_logs."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from fastapi import Request

from app.config import settings
from app.database import background_db_session
from app.models.logs import SkystreamUsersLogs

logger = logging.getLogger("oss")

HELPDESK_PAGE_CALL = "/call"
HELPDESK_PAGE_USER = "/users/{user_id}"


def user_profile_page(user_id: int) -> str:
    return HELPDESK_PAGE_USER.format(user_id=user_id)


def extract_request_meta(request: Optional[Request]) -> dict[str, Any]:
    if request is None:
        return {
            "ip_address": None,
            "user_agent": None,
            "http_method": None,
            "request_path": None,
            "request_id": None,
        }
    ip = request.client.host if request.client else None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        ip = fwd.split(",")[0].strip() or ip
    return {
        "ip_address": ip,
        "user_agent": request.headers.get("user-agent"),
        "http_method": request.method,
        "request_path": str(request.url.path),
        "request_id": request.headers.get("x-request-id"),
    }


async def _persist_skystream_user_log(
    *,
    user_id: int,
    action: str,
    page: str,
    success: bool = True,
    project_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    description: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    http_method: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    action_norm = (action or "").strip().upper()
    if not action_norm:
        logger.warning("skystream_users_logs: empty action, skip")
        return
    eid = None if entity_id is None else str(entity_id)
    try:
        async with background_db_session() as db:
            db.add(
                SkystreamUsersLogs(
                    user_id=int(user_id),
                    project_id=int(
                        project_id
                        if project_id is not None
                        else settings.HELPDESK_SKYSTREAM_PROJECT_ID
                    ),
                    page=page,
                    action=action_norm,
                    success=bool(success),
                    entity_type=entity_type,
                    entity_id=eid,
                    description=description,
                    details=details,
                    error_message=error_message,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    http_method=http_method,
                    request_path=request_path,
                    request_id=request_id,
                )
            )
            await db.commit()
    except Exception:
        logger.exception(
            "skystream_users_logs write failed user_id=%s action=%s page=%s",
            user_id,
            action_norm,
            page,
        )


def schedule_skystream_user_log(
    *,
    user_id: int,
    action: str,
    page: str,
    success: bool = True,
    project_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    description: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    error_message: Optional[str] = None,
    request: Optional[Request] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    http_method: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Поставить запись лога в фон (не блокирует ответ пользователю)."""
    meta = extract_request_meta(request)
    payload = {
        "user_id": int(user_id),
        "action": action,
        "page": page,
        "success": success,
        "project_id": project_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "description": description,
        "details": details,
        "error_message": error_message,
        "ip_address": ip_address if ip_address is not None else meta["ip_address"],
        "user_agent": user_agent if user_agent is not None else meta["user_agent"],
        "http_method": http_method if http_method is not None else meta["http_method"],
        "request_path": request_path if request_path is not None else meta["request_path"],
        "request_id": request_id if request_id is not None else meta["request_id"],
    }
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("skystream_users_logs: no running loop, skip")
        return
    loop.create_task(_persist_skystream_user_log(**payload))
