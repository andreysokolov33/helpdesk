from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk import news_service as news_svc
from app.api.v1.routers.helpdesk.schemas import (
    OperatorNewsBellDigestResponse,
    OperatorNewsBellResponse,
    OperatorNewsDetailResponse,
    OperatorNewsListResponse,
    OperatorNewsMarkReadResponse,
)
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/news", tags=["Helpdesk — новости"])


@router.get("", response_model=OperatorNewsListResponse)
async def operator_news_list(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    limit: int = Query(20, ge=1, le=20),
    offset: int = Query(0, ge=0),
) -> OperatorNewsListResponse:
    """История новостей: актуальные и уже прочитанные (в т.ч. снятые с публикации)."""
    operator_id = int(user["user_id"])
    data = await news_svc.fetch_operator_news_history(
        db,
        operator_id=operator_id,
        limit=limit,
        offset=offset,
    )
    return OperatorNewsListResponse(**data)


@router.get("/bell", response_model=OperatorNewsBellResponse)
async def operator_news_bell(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorNewsBellResponse:
    """Непрочитанные новости для колокольчика."""
    operator_id = int(user["user_id"])
    data = await news_svc.fetch_operator_news_bell(db, operator_id=operator_id)
    return OperatorNewsBellResponse(**data)


@router.get("/bell/digest", response_model=OperatorNewsBellDigestResponse)
async def operator_news_bell_digest(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    digest: str | None = Query(
        None,
        description="Отпечаток с прошлого поллинга; при совпадении changed=false",
    ),
) -> OperatorNewsBellDigestResponse:
    """Лёгкий поллинг счётчика колокольчика."""
    operator_id = int(user["user_id"])
    data = await news_svc.fetch_operator_news_bell_digest(
        db,
        operator_id=operator_id,
        client_digest=(digest or "").strip() or None,
    )
    return OperatorNewsBellDigestResponse(**data)


@router.get("/{news_id}", response_model=OperatorNewsDetailResponse)
async def operator_news_detail(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorNewsDetailResponse:
    """Полная новость (HTML-тело) для модального окна."""
    operator_id = int(user["user_id"])
    row = await news_svc.fetch_operator_news_detail(
        db,
        operator_id=operator_id,
        news_id=news_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Новость не найдена")
    return OperatorNewsDetailResponse(**row)


@router.post("/{news_id}/read", response_model=OperatorNewsMarkReadResponse)
async def operator_news_mark_read(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorNewsMarkReadResponse:
    """Отметить новость прочитанной."""
    operator_id = int(user["user_id"])
    ok = await news_svc.mark_operator_news_read(
        db,
        operator_id=operator_id,
        news_id=news_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Новость не найдена")
    return OperatorNewsMarkReadResponse(ok=True)
