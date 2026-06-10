from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import OperatorTicketMonthStatsResponse
from app.api.v1.routers.helpdesk import ticket_service as ticket_svc
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/operators", tags=["Helpdesk — оператор"])


@router.get("/me/ticket-stats", response_model=OperatorTicketMonthStatsResponse)
async def operator_ticket_month_stats(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorTicketMonthStatsResponse:
    """Статистика тикетов текущего оператора за календарный месяц."""
    uid = int(user["user_id"])
    data = await ticket_svc.fetch_operator_ticket_month_stats(db, user_id=uid, year=year, month=month)
    return OperatorTicketMonthStatsResponse(**data)
