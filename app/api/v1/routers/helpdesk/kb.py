from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import kb_service as kb_svc
from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.kb_schemas import (
    KbArticleDetailResponse,
    KbHomeResponse,
    KbMarkStudiedResponse,
    KbQuizFinishResponse,
    KbQuizSessionResponse,
    KbQuizStartAttemptResponse,
    KbQuizSubmitAnswerRequest,
    KbQuizSubmitAnswerResponse,
    KbSearchResponse,
)
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/kb", tags=["Helpdesk — база знаний"])


@router.get("", response_model=KbHomeResponse)
async def kb_home(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbHomeResponse:
    """Дерево разделов со статьями и прогрессом оператора."""
    operator_id = int(user["user_id"])
    data = await kb_svc.fetch_kb_home(db, operator_id=operator_id)
    return KbHomeResponse(**data)


@router.get("/search", response_model=KbSearchResponse)
async def kb_search(
    q: str = Query("", max_length=200, description="Поиск по заголовку и содержимому"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbSearchResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.search_kb_articles(
        db,
        operator_id=operator_id,
        query=q,
        limit=limit,
    )
    return KbSearchResponse(**data)


@router.get("/articles/{slug}", response_model=KbArticleDetailResponse)
async def kb_article_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbArticleDetailResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.fetch_kb_article_detail(
        db,
        operator_id=operator_id,
        slug=slug,
    )
    await kb_svc.touch_kb_article_view(
        db,
        operator_id=operator_id,
        article_id=int(data["id"]),
    )
    return KbArticleDetailResponse(**data)


@router.post("/articles/{article_id}/studied", response_model=KbMarkStudiedResponse)
async def kb_article_mark_studied(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbMarkStudiedResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.mark_kb_article_studied(
        db,
        operator_id=operator_id,
        article_id=article_id,
    )
    return KbMarkStudiedResponse(**data)


@router.get("/articles/{slug}/quiz", response_model=KbQuizSessionResponse)
async def kb_quiz_session(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbQuizSessionResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.fetch_kb_quiz_session(db, operator_id=operator_id, slug=slug)
    return KbQuizSessionResponse(**data)


@router.post("/articles/{slug}/quiz/attempts", response_model=KbQuizStartAttemptResponse)
async def kb_quiz_start_attempt(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbQuizStartAttemptResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.start_kb_quiz_attempt(db, operator_id=operator_id, slug=slug)
    return KbQuizStartAttemptResponse(**data)


@router.post(
    "/quiz-attempts/{attempt_id}/answers",
    response_model=KbQuizSubmitAnswerResponse,
)
async def kb_quiz_submit_answer(
    attempt_id: int,
    body: KbQuizSubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbQuizSubmitAnswerResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.submit_kb_quiz_answer(
        db,
        operator_id=operator_id,
        attempt_id=attempt_id,
        question_id=body.question_id,
        selected_option_ids=body.selected_option_ids,
    )
    return KbQuizSubmitAnswerResponse(**data)


@router.post("/quiz-attempts/{attempt_id}/finish", response_model=KbQuizFinishResponse)
async def kb_quiz_finish_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> KbQuizFinishResponse:
    operator_id = int(user["user_id"])
    data = await kb_svc.finish_kb_quiz_attempt(
        db,
        operator_id=operator_id,
        attempt_id=attempt_id,
    )
    return KbQuizFinishResponse(**data)
