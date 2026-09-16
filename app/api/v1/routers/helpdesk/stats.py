from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth.dao import SkystreamUsersDAO
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk import admin_quiz_stats_service as admin_quiz_svc
from app.api.v1.routers.helpdesk import operator_quiz_review_service as quiz_review_svc
from app.api.v1.routers.helpdesk import operator_quiz_stats_service as quiz_stats_svc
from app.api.v1.routers.helpdesk import stats_service as stats_svc
from app.api.v1.routers.helpdesk.operator_quiz_schemas import OperatorQuizAttemptReviewResponse
from app.api.v1.routers.helpdesk.stats_schemas import (
    AdminQuizAttemptsPageResponse,
    QuizTrainingDashboardResponse,
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
        admin_view=admin,
    )

    return StatsDashboardResponse(
        summary=summary,
        operators=operators,
        recent_ratings=recent_ratings,
        operator_options=operator_options,
    )


@router.get("/quiz-training", response_model=QuizTrainingDashboardResponse)
async def stats_quiz_training(
    date_from: date | None = Query(None, description="Начало периода для ежедневных тестов"),
    date_to: date | None = Query(None, description="Конец периода для ежедневных тестов"),
    operator_id: int | None = Query(None, description="Детальная статистика оператора"),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> QuizTrainingDashboardResponse:
    if date_from is None or date_to is None:
        date_from, date_to = _default_period()
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть позже date_to")

    level = await _viewer_level(db, user)
    admin = stats_svc.is_support_admin(role=user.get("role"), level=level)
    if not admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    if operator_id is not None:
        op_row = await SkystreamUsersDAO.find_one_or_none(db, id=operator_id)
        if not op_row or op_row.get("role") != "support":
            raise HTTPException(status_code=404, detail="Оператор не найден")

    data = await admin_quiz_svc.fetch_admin_quiz_training(
        db,
        date_from=date_from,
        date_to=date_to,
        detail_operator_id=operator_id,
    )
    return QuizTrainingDashboardResponse(**data)


async def _require_admin_and_operator(
    db: AsyncSession, user: dict[str, Any], operator_id: int
) -> str:
    level = await _viewer_level(db, user)
    admin = stats_svc.is_support_admin(role=user.get("role"), level=level)
    if not admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    op_row = await SkystreamUsersDAO.find_one_or_none(db, id=operator_id)
    if not op_row or op_row.get("role") != "support":
        raise HTTPException(status_code=404, detail="Оператор не найден")
    return (op_row.get("full_name") or op_row.get("login") or "").strip() or f"#{operator_id}"


@router.get(
    "/quiz-training/operators/{operator_id}/attempts",
    response_model=AdminQuizAttemptsPageResponse,
)
async def stats_quiz_training_operator_attempts(
    operator_id: int,
    attempt_type: str = Query(
        "daily_warmup",
        pattern="^(daily_warmup|kb_topic)$",
        description="Тип попыток: ежедневные тесты или тесты по статьям БЗ",
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> AdminQuizAttemptsPageResponse:
    """Постраничный список попыток оператора данного типа (от новых к старым) — для админа."""
    operator_name = await _require_admin_and_operator(db, user, operator_id)

    data = await quiz_stats_svc.fetch_operator_attempts_page(
        db,
        operator_id=operator_id,
        attempt_type=attempt_type,
        page=page,
        per_page=per_page,
    )
    return AdminQuizAttemptsPageResponse(
        operator_id=operator_id,
        operator_name=operator_name,
        attempt_type=attempt_type,
        page=page,
        per_page=per_page,
        total=data["total"],
        passed_count=data["passed_count"],
        avg_mistakes=data["avg_mistakes"],
        avg_score_percent=data["avg_score_percent"],
        attempts=data["items"],
    )


@router.get(
    "/quiz-training/operators/{operator_id}/attempts/{attempt_id}/review",
    response_model=OperatorQuizAttemptReviewResponse,
)
async def stats_quiz_training_operator_attempt_review(
    operator_id: int,
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorQuizAttemptReviewResponse:
    """Полный разбор одной попытки (вопросы, варианты, выбор оператора) — для админа."""
    await _require_admin_and_operator(db, user, operator_id)

    data = await quiz_review_svc.fetch_attempt_review(
        db,
        operator_id=operator_id,
        attempt_id=attempt_id,
    )
    return OperatorQuizAttemptReviewResponse(**data)
