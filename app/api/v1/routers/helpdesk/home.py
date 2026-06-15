from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk import home_service as home_svc
from app.api.v1.routers.helpdesk import ticket_service as ticket_svc
from app.api.v1.routers.helpdesk.schemas import (
    HomeDashboardDigestResponse,
    HomeDashboardResponse,
    HomeRatingItem,
    HomeTicketsDigestResponse,
    HomeTicketsResponse,
)
from app.api.v1.routers.helpdesk.tracker import map_tracker_list_rows_to_items
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/home", tags=["Helpdesk — главная"])


@router.get("/tickets", response_model=HomeTicketsResponse)
async def home_tickets(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> HomeTicketsResponse:
    """Тикеты для главной: «ждут ответа» (до 3) и «открытые» (до 7)."""
    viewer_id = int(user["user_id"])
    bundle = await ticket_svc.fetch_home_tickets_bundle(db, viewer_id=viewer_id)
    needs_reply = map_tracker_list_rows_to_items(bundle["needs_reply"], user)
    open_items = map_tracker_list_rows_to_items(bundle["open"], user)
    return HomeTicketsResponse(
        total_open=int(bundle["total_open"]),
        needs_reply_count=int(bundle["needs_reply_count"]),
        needs_reply=needs_reply,
        open=open_items,
    )


@router.get("/tickets/digest", response_model=HomeTicketsDigestResponse)
async def home_tickets_digest(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    digest: Optional[str] = Query(
        None,
        description="Отпечаток с прошлого поллинга; при совпадении changed=false",
    ),
) -> HomeTicketsDigestResponse:
    """Лёгкий поллинг тикетов на главной."""
    viewer_id = int(user["user_id"])
    data = await ticket_svc.fetch_home_tickets_digest(
        db,
        viewer_id=viewer_id,
        client_digest=(digest or "").strip() or None,
    )
    return HomeTicketsDigestResponse(**data)


@router.get("/dashboard", response_model=HomeDashboardResponse)
async def home_dashboard(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> HomeDashboardResponse:
    """Последние оценки по тикетам, где оператор был исполнителем или участником."""
    viewer_id = int(user["user_id"])
    rows = await home_svc.fetch_home_recent_ratings(db, viewer_id=viewer_id, limit=5)
    ratings = [HomeRatingItem(**r) for r in rows]
    return HomeDashboardResponse(ratings=ratings)


@router.get("/dashboard/digest", response_model=HomeDashboardDigestResponse)
async def home_dashboard_digest(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    digest: Optional[str] = Query(
        None,
        description="Отпечаток с прошлого поллинга; при совпадении changed=false",
    ),
) -> HomeDashboardDigestResponse:
    """Лёгкий поллинг блока оценок на главной."""
    viewer_id = int(user["user_id"])
    data = await home_svc.fetch_home_ratings_digest(
        db,
        viewer_id=viewer_id,
        client_digest=(digest or "").strip() or None,
    )
    return HomeDashboardDigestResponse(**data)
