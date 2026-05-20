from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import DeskSearchResponse, DeskSearchSubscriberHit
from app.api.v1.routers.users.dao import UsersDAO
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/search", tags=["Helpdesk — поиск"])


@router.get("", response_model=DeskSearchResponse)
async def desk_search(
    q: str = Query(..., min_length=2, max_length=200, description="Строка поиска"),
    limit: int = Query(15, ge=1, le=30),
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> DeskSearchResponse:
    rows = await UsersDAO.search_subscribers(db, q, limit=limit)
    subscribers = [DeskSearchSubscriberHit(**row) for row in rows]
    # База знаний — заглушка, подключим позже
    return DeskSearchResponse(subscribers=subscribers, kb=[])
