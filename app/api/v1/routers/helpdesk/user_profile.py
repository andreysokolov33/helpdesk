from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.password_reset_schemas import (
    PasswordResetGenerateResponse,
    PasswordResetPollResponse,
    PasswordResetStateResponse,
)
from app.api.v1.routers.helpdesk.fast_check_schemas import FastCheckResponse
from app.api.v1.routers.helpdesk.user_profile_schemas import (
    ActionMessage,
    FreezeRequest,
    PaymentHistoryListResponse,
    TariffBlockResponse,
    TariffHistoryListResponse,
    ProfileTicketListResponse,
    UserProfileResponse,
)
from app.api.v1.routers.helpdesk import fast_check_service as fc_svc
from app.api.v1.routers.helpdesk import password_reset_service as pwd_svc
from app.api.v1.routers.helpdesk import user_profile_service as svc
from app.database import get_db

router = APIRouter(prefix="/v1/helpdesk/users", tags=["Helpdesk — абонент"])


@router.get("/{user_id}/payments", response_model=PaymentHistoryListResponse)
async def list_user_payments(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentHistoryListResponse:
    return await svc.load_user_payments_page(db, user_id, page=page, per_page=per_page)


@router.get("/{user_id}/tariff-history", response_model=TariffHistoryListResponse)
async def list_user_tariff_history(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> TariffHistoryListResponse:
    return await svc.load_user_tariff_history_page(db, user_id, page=page, per_page=per_page)


@router.get("/{user_id}/profile/tickets", response_model=ProfileTicketListResponse)
async def list_user_profile_tickets(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileTicketListResponse:
    return await svc.load_user_tickets_page(db, user_id, page=page, per_page=per_page)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_profile(
    user_id: int,
    tickets_page: int = Query(1, ge=1),
    tickets_per_page: int = Query(10, ge=0, le=50),
    include_tickets: bool = Query(False),
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    return await svc.get_user_profile(
        db,
        user_id,
        tickets_page,
        tickets_per_page,
        include_tickets=include_tickets and tickets_per_page > 0,
    )


@router.post("/{user_id}/unarchive", response_model=ActionMessage)
async def unarchive(
    user_id: int,
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ActionMessage:
    return await svc.unarchive_user(db, user_id)


@router.post("/{user_id}/unfreeze", response_model=ActionMessage)
async def unfreeze(
    user_id: int,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ActionMessage:
    return await svc.unfreeze_tariff(db, user_id, operator, request)


@router.delete("/{user_id}/freeze-plan", response_model=ActionMessage)
async def cancel_freeze_plan(
    user_id: int,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ActionMessage:
    return await svc.delete_planned_freeze(db, user_id, operator, request)


@router.post("/{user_id}/tariff/remove-ended", response_model=TariffBlockResponse)
async def remove_ended_tariff(
    user_id: int,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> TariffBlockResponse:
    return await svc.remove_ended_tariff(db, user_id, operator, request)


@router.post("/{user_id}/freeze", response_model=ActionMessage)
async def freeze(
    user_id: int,
    body: FreezeRequest,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ActionMessage:
    return await svc.apply_freeze(
        db, user_id, body.date_freeze, body.date_unfreeze, operator, request
    )


@router.get("/{user_id}/password-reset", response_model=PasswordResetStateResponse)
async def password_reset_state(
    user_id: int,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordResetStateResponse:
    return await pwd_svc.get_password_reset_state(db, user_id, operator, request)


@router.post("/{user_id}/password-reset/generate", response_model=PasswordResetGenerateResponse)
async def password_reset_generate(
    user_id: int,
    request: Request,
    operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordResetGenerateResponse:
    return await pwd_svc.generate_password_reset_code(db, user_id, operator, request)


@router.get("/{user_id}/password-reset/poll", response_model=PasswordResetPollResponse)
async def password_reset_poll(
    user_id: int,
    code_id: int | None = None,
    _operator: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordResetPollResponse:
    return await pwd_svc.poll_password_reset_status(db, user_id, code_id)


@router.post("/{user_id}/fast-check", response_model=FastCheckResponse)
async def fast_check(
    user_id: int,
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> FastCheckResponse:
    return await fc_svc.run_fast_check(db, user_id)


@router.post("/{user_id}/disconnect-sessions", response_model=ActionMessage)
async def disconnect_sessions(
    user_id: int,
    _user: dict = Depends(require_tracker_user),
    db: AsyncSession = Depends(get_db),
) -> ActionMessage:
    from app.api.v1.routers.users.dao import UsersDAO

    u = await UsersDAO.find_one_or_none(db, id=user_id)
    if not u:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Абонент не найден")
    login = (u.get("login") or "").strip()
    return await svc.force_disconnect(db, user_id, login)
