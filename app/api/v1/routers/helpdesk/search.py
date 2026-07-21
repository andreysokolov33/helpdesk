from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import kb_service as kb_svc
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import (
    DeskSearchKbHit,
    DeskSearchResponse,
    DeskSearchSubscriberHit,
)
from app.api.v1.routers.users.dao import UsersDAO
from app.constants import TRACKER_HELPDESK_LIST_SOURCES, TRACKER_OPEN_STATUSES
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/search", tags=["Helpdesk — поиск"])


async def _fetch_open_ticket_ids_by_subscriber(
    db: AsyncSession,
    *,
    subscriber_ids: list[int],
    per_subscriber_limit: int = 5,
) -> dict[int, list[int]]:
    if not subscriber_ids:
        return {}

    status_in = ", ".join(f"'{status}'::users.tracker_status" for status in TRACKER_OPEN_STATUSES)
    source_in = ", ".join(f"'{source}'" for source in TRACKER_HELPDESK_LIST_SOURCES)

    sql = text(
        f"""
        WITH ranked AS (
            SELECT
                tt.user_id,
                tt.id AS ticket_id,
                ROW_NUMBER() OVER (
                    PARTITION BY tt.user_id
                    ORDER BY COALESCE(tt.updated_at, tt.date_of_create) DESC, tt.id DESC
                ) AS rn
            FROM users.tracker_tickets tt
            WHERE tt.user_id = ANY(:subscriber_ids)
              AND tt.status IN ({status_in})
              AND COALESCE(tt.source, 'call_center') IN ({source_in})
        )
        SELECT user_id, ticket_id
        FROM ranked
        WHERE rn <= :per_subscriber_limit
        ORDER BY user_id, rn
        """
    )
    rows = (await db.execute(
        sql,
        {
            "subscriber_ids": subscriber_ids,
            "per_subscriber_limit": per_subscriber_limit,
        },
    )).mappings().all()

    out: dict[int, list[int]] = {}
    for row in rows:
        uid = int(row["user_id"])
        out.setdefault(uid, []).append(int(row["ticket_id"]))
    return out


@router.get("", response_model=DeskSearchResponse)
async def desk_search(
    q: str = Query(..., min_length=2, max_length=200, description="Строка поиска"),
    limit: int = Query(15, ge=1, le=30),
    user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> DeskSearchResponse:
    rows = await UsersDAO.search_subscribers(db, q, limit=limit)
    subscriber_ids = [int(row["id"]) for row in rows if row.get("id") is not None]
    open_tickets_by_subscriber = await _fetch_open_ticket_ids_by_subscriber(
        db,
        subscriber_ids=subscriber_ids,
    )
    subscribers = [
        DeskSearchSubscriberHit(
            **row,
            open_ticket_ids=open_tickets_by_subscriber.get(int(row["id"]), []),
        )
        for row in rows
    ]

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
