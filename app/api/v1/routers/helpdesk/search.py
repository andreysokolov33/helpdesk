from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import kb_service as kb_svc
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import (
    DeskSearchKbHit,
    DeskSearchResponse,
    DeskSearchSubscriberHit,
)
from app.api.v1.routers.users.dao import UsersDAO
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/search", tags=["Helpdesk — поиск"])


@router.get("", response_model=DeskSearchResponse)
async def desk_search(
    q: str = Query(..., min_length=2, max_length=200, description="Строка поиска"),
    limit: int = Query(15, ge=1, le=30),
    user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> DeskSearchResponse:
    rows = await UsersDAO.search_subscribers(db, q, limit=limit)
    subscribers = [DeskSearchSubscriberHit(**row) for row in rows]

    operator_id = int(user["user_id"])
    kb_limit = min(limit, 10)
    kb_data = await kb_svc.search_kb_articles(
        db,
        operator_id=operator_id,
        query=q,
        limit=kb_limit,
    )
    kb = [
        DeskSearchKbHit(
            id=int(item["id"]),
            slug=str(item["slug"]),
            title=str(item["title"]),
            excerpt=item.get("summary") or item.get("subtitle"),
        )
        for item in kb_data.get("items", [])
    ]

    return DeskSearchResponse(subscribers=subscribers, kb=kb)
