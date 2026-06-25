from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import daily_quiz_service as daily_svc
from app.api.v1.routers.helpdesk import kb_service as kb_svc
from app.api.v1.routers.helpdesk.daily_quiz_schemas import (
    DailyQuizFinishResponse,
    DailyQuizSessionResponse,
    DailyQuizStartAttemptResponse,
    DailyQuizStatusResponse,
    DailyQuizSubmitAnswerResponse,
)
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.kb_schemas import KbQuizSubmitAnswerRequest
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/daily-quiz", tags=["Helpdesk — ежедневный тест"])


def _operator_ctx(user: dict[str, Any]) -> tuple[int, str | None, int | None]:
    return int(user["user_id"]), user.get("role"), user.get("level")


@router.get("/status", response_model=DailyQuizStatusResponse)
async def daily_quiz_status(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> DailyQuizStatusResponse:
    operator_id, role, level = _operator_ctx(user)
    data = await daily_svc.fetch_daily_quiz_status(
        db, operator_id=operator_id, role=role, level=level
    )
    return DailyQuizStatusResponse(**data)


@router.get("/session", response_model=DailyQuizSessionResponse)
async def daily_quiz_session(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> DailyQuizSessionResponse:
    operator_id, role, level = _operator_ctx(user)
    data = await daily_svc.fetch_daily_quiz_session(
        db, operator_id=operator_id, role=role, level=level
    )
    return DailyQuizSessionResponse(**data)


@router.post("/attempts", response_model=DailyQuizStartAttemptResponse)
async def daily_quiz_start_attempt(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> DailyQuizStartAttemptResponse:
    operator_id, role, level = _operator_ctx(user)
    data = await daily_svc.start_daily_quiz_attempt(
        db, operator_id=operator_id, role=role, level=level
    )
    return DailyQuizStartAttemptResponse(**data)


@router.post(
    "/quiz-attempts/{attempt_id}/answers",
    response_model=DailyQuizSubmitAnswerResponse,
)
async def daily_quiz_submit_answer(
    attempt_id: int,
    body: KbQuizSubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> DailyQuizSubmitAnswerResponse:
    operator_id, _, _ = _operator_ctx(user)
    data = await kb_svc.submit_kb_quiz_answer(
        db,
        operator_id=operator_id,
        attempt_id=attempt_id,
        question_id=body.question_id,
        selected_option_ids=body.selected_option_ids,
    )
    return DailyQuizSubmitAnswerResponse(**data)


@router.post("/quiz-attempts/{attempt_id}/finish", response_model=DailyQuizFinishResponse)
async def daily_quiz_finish_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> DailyQuizFinishResponse:
    operator_id, _, _ = _operator_ctx(user)
    data = await kb_svc.finish_kb_quiz_attempt(
        db,
        operator_id=operator_id,
        attempt_id=attempt_id,
    )
    return DailyQuizFinishResponse(**data)
