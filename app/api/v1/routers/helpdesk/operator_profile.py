from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk import operators_admin_service as ops_admin_svc
from app.api.v1.routers.helpdesk.schemas import (
    OperatorCreateRequest,
    OperatorManageItem,
    OperatorManageListResponse,
    OperatorPasswordResetRequest,
    OperatorSuggestedLoginResponse,
    OperatorTicketMonthStatsResponse,
    OperatorUpdateRequest,
)
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


@router.post("/me/presence", status_code=204)
async def operator_presence_heartbeat(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> None:
    """Пульс активности вкладки (онлайн-статус оператора)."""
    await ops_admin_svc.touch_presence(db, int(user["user_id"]))


@router.get("/manage", response_model=OperatorManageListResponse)
async def operators_manage_list(
    page: int = Query(1, ge=1, description="Страница списка операторов"),
    per_page: int = Query(
        ops_admin_svc.OPERATORS_MANAGE_PER_PAGE_DEFAULT,
        ge=1,
        le=100,
        description="Операторов на странице",
    ),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorManageListResponse:
    await ops_admin_svc.require_support_admin(db, user)
    data = await ops_admin_svc.fetch_operators_manage(db, page=page, per_page=per_page)
    return OperatorManageListResponse(**data)


@router.get("/manage/suggested-login", response_model=OperatorSuggestedLoginResponse)
async def operators_suggested_login(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorSuggestedLoginResponse:
    await ops_admin_svc.require_support_admin(db, user)
    login = await ops_admin_svc.fetch_suggested_login(db)
    return OperatorSuggestedLoginResponse(login=login)


@router.post("/manage", response_model=OperatorManageItem, status_code=201)
async def operators_create(
    body: OperatorCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorManageItem:
    await ops_admin_svc.require_support_admin(db, user)
    item = await ops_admin_svc.create_operator(
        db,
        login=body.login,
        password=body.password,
        full_name=body.full_name,
        email=body.email,
        granted_by=int(user["user_id"]),
    )
    return OperatorManageItem(**item)


@router.patch("/manage/{operator_id}", response_model=OperatorManageItem)
async def operators_update(
    operator_id: int,
    body: OperatorUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> OperatorManageItem:
    await ops_admin_svc.require_support_admin(db, user)
    if body.full_name is None and body.is_active is None:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    item = await ops_admin_svc.update_operator(
        db,
        operator_id=operator_id,
        viewer_id=int(user["user_id"]),
        full_name=body.full_name,
        is_active=body.is_active,
    )
    return OperatorManageItem(**item)


@router.post("/manage/{operator_id}/password", status_code=204)
async def operators_reset_password(
    operator_id: int,
    body: OperatorPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> None:
    await ops_admin_svc.require_support_admin(db, user)
    await ops_admin_svc.reset_operator_password(
        db,
        operator_id=operator_id,
        viewer_id=int(user["user_id"]),
        password=body.password,
    )
