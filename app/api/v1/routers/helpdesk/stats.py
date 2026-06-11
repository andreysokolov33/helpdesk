from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth.dao import SkystreamUsersDAO
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk import stats_service as stats_svc
from app.api.v1.routers.helpdesk.stats_schemas import (
    StatsDashboardResponse,
    StatsSummaryResponse,
    SupportOperatorOption,
)
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/stats", tags=["Helpdesk — статистика"])


def _default_period() -> tuple[date, date]:
    today = date.today()
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])
    return month_start, month_end


async def _viewer_level(db: AsyncSession, user: dict[str, Any]) -> int | None:
    row = await SkystreamUsersDAO.find_one_or_none(db, id=int(user["user_id"]))
    if not row:
        return None
    level = row.get("level")
    return int(level) if level is not None else None


@router.get("/dashboard", response_model=StatsDashboardResponse)
async def stats_dashboard(
    date_from: date | None = Query(None, description="Начало периода (включительно)"),
    date_to: date | None = Query(None, description="Конец периода (включительно)"),
    operator_id: int | None = Query(None, description="Фильтр по оператору (только admin)"),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> StatsDashboardResponse:
    if date_from is None or date_to is None:
        date_from, date_to = _default_period()
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть позже date_to")

    uid = int(user["user_id"])
    role = user.get("role")
    level = await _viewer_level(db, user)
    admin = stats_svc.is_support_admin(role=role, level=level)

    scope_operator_id: int | None
    operator_name: str | None = None
    operator_options: list[SupportOperatorOption] = []

    if admin:
        operator_options = [
            SupportOperatorOption(id=int(o["id"]), label=str(o["label"]))
            for o in await stats_svc.fetch_support_operators(db)
        ]
        if operator_id is not None:
            op_row = await SkystreamUsersDAO.find_one_or_none(db, id=operator_id)
            if not op_row or op_row.get("role") != "support":
                raise HTTPException(status_code=404, detail="Оператор не найден")
            scope_operator_id = operator_id
            operator_name = (op_row.get("full_name") or op_row.get("login") or "").strip() or None
        else:
            scope_operator_id = None
    else:
        if operator_id is not None and operator_id != uid:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        scope_operator_id = uid
        operator_name = (user.get("full_name") or user.get("login") or "").strip() or None

    summary_data = await stats_svc.fetch_stats_summary(
        db,
        date_from=date_from,
        date_to=date_to,
        operator_id=scope_operator_id,
    )
    summary = StatsSummaryResponse(
        **summary_data,
        is_admin_view=admin,
        operator_id=scope_operator_id,
        operator_name=operator_name,
    )

    operators = []
    if admin and operator_id is None:
        operators = await stats_svc.fetch_operator_stats_rows(
            db, date_from=date_from, date_to=date_to
        )

    recent_ratings = await stats_svc.fetch_recent_ratings(
        db,
        date_from=date_from,
        date_to=date_to,
        operator_id=scope_operator_id,
        limit=10,
    )

    return StatsDashboardResponse(
        summary=summary,
        operators=operators,
        recent_ratings=recent_ratings,
        operator_options=operator_options,
    )
