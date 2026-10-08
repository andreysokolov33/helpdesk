from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import training_service as training_svc
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.training_schemas import (
    TrainingActiveSessionResponse,
    TrainingAdminOperatorSessionsResponse,
    TrainingAdminOperatorsResponse,
    TrainingAdminSummaryResponse,
    TrainingLeadersResponse,
    TrainingMySessionsResponse,
    TrainingNextQuestionResponse,
    TrainingSessionState,
    TrainingSourcesResponse,
    TrainingStartRequest,
    TrainingSubmitAnswerRequest,
    TrainingSubmitAnswerResponse,
)
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/training", tags=["Helpdesk — тренажёр"])


def _operator_id(user: dict[str, Any]) -> int:
    return int(user["user_id"])


def _period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    if date_from is None or date_to is None:
        today = date.today()
        date_from = today.replace(day=1)
        date_to = today.replace(day=monthrange(today.year, today.month)[1])
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть позже date_to")
    return date_from, date_to


async def _require_admin(db: AsyncSession, user: dict[str, Any]) -> None:
    if not await training_svc.is_training_admin(db, user):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


# ---------------------------------------------------------------------------
# Оператор
# ---------------------------------------------------------------------------


@router.get("/sources", response_model=TrainingSourcesResponse)
async def training_sources(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingSourcesResponse:
    """Источники вопросов: ежедневный пул и тесты статей по разделам."""
    data = await training_svc.fetch_training_sources(db)
    return TrainingSourcesResponse(**data)


@router.get("/sessions/active", response_model=TrainingActiveSessionResponse)
async def training_active_session(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingActiveSessionResponse:
    data = await training_svc.fetch_active_session(db, operator_id=_operator_id(user))
    return TrainingActiveSessionResponse(session=data)


@router.get("/sessions", response_model=TrainingMySessionsResponse)
async def training_my_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingMySessionsResponse:
    """История сессий текущего пользователя (от новых к старым) и итоги за всё время."""
    data = await training_svc.fetch_my_sessions(
        db, operator_id=_operator_id(user), page=page, per_page=per_page
    )
    return TrainingMySessionsResponse(**data)


@router.post("/sessions", response_model=TrainingSessionState)
async def training_start_session(
    body: TrainingStartRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingSessionState:
    """Начать сессию. Активная сессия пользователя (если есть) закрывается."""
    data = await training_svc.start_training_session(
        db,
        operator_id=_operator_id(user),
        source_type=body.source_type,
        article_id=body.article_id,
        category_id=body.category_id,
        all_articles=body.all_articles,
    )
    return TrainingSessionState(**data)


@router.get("/sessions/{session_id}", response_model=TrainingSessionState)
async def training_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingSessionState:
    data = await training_svc.fetch_session(
        db, operator_id=_operator_id(user), session_id=session_id
    )
    return TrainingSessionState(**data)


@router.get("/sessions/{session_id}/next", response_model=TrainingNextQuestionResponse)
async def training_next_question(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingNextQuestionResponse:
    """Текущий неотвеченный вопрос либо следующий из перемешанного круга."""
    data = await training_svc.next_training_question(
        db, operator_id=_operator_id(user), session_id=session_id
    )
    return TrainingNextQuestionResponse(**data)


@router.post("/sessions/{session_id}/answers", response_model=TrainingSubmitAnswerResponse)
async def training_submit_answer(
    session_id: int,
    body: TrainingSubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingSubmitAnswerResponse:
    data = await training_svc.submit_training_answer(
        db,
        operator_id=_operator_id(user),
        session_id=session_id,
        question_id=body.question_id,
        selected_option_ids=body.selected_option_ids,
    )
    return TrainingSubmitAnswerResponse(**data)


@router.post("/sessions/{session_id}/finish", response_model=TrainingSessionState)
async def training_finish_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingSessionState:
    data = await training_svc.finish_training_session(
        db, operator_id=_operator_id(user), session_id=session_id
    )
    return TrainingSessionState(**data)


# ---------------------------------------------------------------------------
# Администратор: подчинённые операторы (support, level=1)
# ---------------------------------------------------------------------------


@router.get("/admin/summary", response_model=TrainingAdminSummaryResponse)
async def training_admin_summary(
    date_from: date | None = Query(None, description="Начало периода по answered_at (включительно)"),
    date_to: date | None = Query(None, description="Конец периода по answered_at (включительно)"),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingAdminSummaryResponse:
    await _require_admin(db, user)
    date_from, date_to = _period(date_from, date_to)
    data = await training_svc.fetch_admin_summary(db, date_from=date_from, date_to=date_to)
    return TrainingAdminSummaryResponse(**data)


@router.get("/admin/leaders", response_model=TrainingLeadersResponse)
async def training_admin_leaders(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingLeadersResponse:
    """Лидеры: байесовское сглаживание (correct + k·p0) / (total + k), k = 20."""
    await _require_admin(db, user)
    date_from, date_to = _period(date_from, date_to)
    data = await training_svc.fetch_admin_leaders(db, date_from=date_from, date_to=date_to)
    return TrainingLeadersResponse(**data)


@router.get("/admin/operators", response_model=TrainingAdminOperatorsResponse)
async def training_admin_operators(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingAdminOperatorsResponse:
    await _require_admin(db, user)
    date_from, date_to = _period(date_from, date_to)
    data = await training_svc.fetch_admin_operators(db, date_from=date_from, date_to=date_to)
    return TrainingAdminOperatorsResponse(**data)


@router.get(
    "/admin/operators/{operator_id}/sessions",
    response_model=TrainingAdminOperatorSessionsResponse,
)
async def training_admin_operator_sessions(
    operator_id: int,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TrainingAdminOperatorSessionsResponse:
    """Сессии подчинённого, в которых есть ответы за период."""
    await _require_admin(db, user)
    date_from, date_to = _period(date_from, date_to)
    operator = await training_svc.find_subordinate(db, operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Оператор не найден")
    data = await training_svc.fetch_admin_operator_sessions(
        db,
        operator_id=operator_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return TrainingAdminOperatorSessionsResponse(
        operator_id=operator_id,
        operator_name=str(operator["operator_name"]),
        **data,
    )
