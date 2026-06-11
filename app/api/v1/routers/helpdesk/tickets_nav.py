from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import UnreadTicketsResponse
from app.api.v1.routers.helpdesk import ticket_service as ticket_svc
from app.database import get_db, redis_client

router = APIRouter(prefix="/v1/helpdesk/tickets", tags=["Helpdesk — тикеты"])

_UNREAD_CACHE_TTL = 10


@router.get("/unread_count", response_model=UnreadTicketsResponse)
async def get_unread_tickets_count(
    user: dict[str, Any] = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadTicketsResponse:
    """Счётчик вкладки «Тикеты»: админ — открытые; оператор — тикеты, где нужен ответ."""
    user_id = int(user["user_id"])
    cache_key = f"unread_stats:{user_id}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            if isinstance(data, dict) and "unread_count" in data:
                return UnreadTicketsResponse(unread_count=int(data["unread_count"]))
    except Exception:
        pass

    count = await ticket_svc.count_tickets_nav_badge(
        db,
        viewer_id=user_id,
        viewer_role=user.get("role"),
        viewer_level=user.get("level"),
    )
    result = UnreadTicketsResponse(unread_count=count)
    try:
        await redis_client.setex(cache_key, _UNREAD_CACHE_TTL, result.model_dump_json())
    except Exception:
        pass
    return result
