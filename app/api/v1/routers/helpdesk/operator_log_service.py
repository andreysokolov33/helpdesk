from __future__ import annotations

from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logs import HelpdeskOperatorLog


async def write_operator_log(
    session: AsyncSession,
    *,
    operator_id: int,
    action: str,
    subscriber_id: Optional[int] = None,
    page: Optional[str] = None,
    request: Optional[Request] = None,
    password_reset_code_id: Optional[int] = None,
    subject_type: Optional[str] = None,
    subject_id: Optional[int] = None,
    details: Optional[dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    auto_commit: bool = False,
) -> dict[str, Any]:
    client_ip = None
    user_agent = None
    http_method = None
    request_path = None
    if request is not None:
        if request.client:
            client_ip = request.client.host
        user_agent = request.headers.get("user-agent")
        http_method = request.method
        request_path = str(request.url.path)

    row = HelpdeskOperatorLog(
        operator_id=operator_id,
        action=action,
        page=page,
        subscriber_id=subscriber_id,
        subject_type=subject_type,
        subject_id=subject_id,
        password_reset_code_id=password_reset_code_id,
        details=details,
        http_method=http_method,
        request_path=request_path,
        client_ip=client_ip,
        user_agent=user_agent,
        success=success,
        error_message=error_message,
    )
    session.add(row)
    await session.flush()
    return {
        "id": row.id,
        "created_at": row.created_at,
    }
