import bcrypt
import logging
from ipaddress import ip_address as parse_ip

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as parse_ua

from app.api.v1.routers.auth.dao import (
    OssUserTokensDAO,
    SkystreamUserProjectAccessDAO,
    SkystreamUsersDAO,
    SubscriberDAO,
)
from app.api.v1.routers.auth.schemas import LoginRequest
from app.core.auth_utils import create_token, decode_jwt_token
from app.database import background_db_session, get_db
from app.utils.redis_functions import (
    get_block_time_left,
    incr_failed_attempts,
    is_blocked,
    reset_failed_attempts,
)

logger = logging.getLogger("oss")

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_client_ip(request: Request) -> str | None:
    for header in ("x-forwarded-for", "x-real-ip"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _is_private_ip(ip_str: str | None) -> bool:
    if not ip_str:
        return True
    try:
        ip = parse_ip(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return True


def _get_device_info(request: Request) -> str:
    ua_string = request.headers.get("user-agent", "Unknown")
    ua = parse_ua(ua_string)
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
    os_info = f"{ua.os.family} {ua.os.version_string}".strip()
    parts = [p for p in [browser, os_info] if p and p.lower() != "none"]
    return " — ".join(parts) or "Unknown Device"


async def _set_auth_cookies(
    response: Response,
    access_token: str,
    access_expire,
    refresh_token: str,
    refresh_expire,
) -> None:
    common = {"path": "/", "httponly": True, "samesite": "lax", "secure": True}
    response.set_cookie(key="oss_acc_token", value=access_token, expires=access_expire, **common)
    response.set_cookie(key="oss_ref_token", value=refresh_token, expires=refresh_expire, **common)
    response.set_cookie(key="oss_login", value="1", expires=access_expire, **common)


async def _record_login_history(user_id: int, ip: str | None, success: bool) -> None:
    try:
        async with background_db_session() as db:
            from app.models.users import AbsLoginHistory
            from app.dao.base import BaseDAO

            class _HistoryDAO(BaseDAO[AbsLoginHistory]):
                model = AbsLoginHistory

            await _HistoryDAO.add(db, user_id=user_id, success=success, ip_address=ip)
    except Exception as e:
        logger.warning(f"Failed to record login history for user {user_id}: {e}")


async def authenticate_user(
    db: AsyncSession,
    login: str,
    password: str,
    ip: str | None,
) -> tuple[dict | None, str | None]:
    """Возвращает (user, None) при успехе; (None, reason) при отказе (reason для ответа API)."""
    user = await SkystreamUsersDAO.find_by_lower_login(db, login=login)
    if not user:
        await incr_failed_attempts(login)
        return None, None

    if not user.get("is_active"):
        await incr_failed_attempts(login)
        return None, None

    stored_hash = user.get("password_hash")
    if not stored_hash:
        await incr_failed_attempts(login)
        return None, None

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        await incr_failed_attempts(login)
        logger.debug(f"User {user['id']} failed login: wrong password")
        return None, None

    uid = int(user["id"])
    if not await SkystreamUserProjectAccessDAO.user_can_login_helpdesk(db, uid):
        await incr_failed_attempts(login)
        logger.info(f"User {uid} login denied: no helpdesk project access")
        return None, "no_project_access"

    return user, None


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    bg_task: BackgroundTasks,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    real_ip = _get_client_ip(request)

    if await is_blocked(data.login):
        time_left = await get_block_time_left(data.login)
        raise HTTPException(
            status_code=403,
            detail=f"Превышено количество попыток. Попробуйте через {time_left}.",
        )

    user, auth_err = await authenticate_user(db, data.login, data.password, real_ip)

    if auth_err == "no_project_access":
        raise HTTPException(
            status_code=403,
            detail="Нет доступа к этому порталу для вашей учётной записи.",
        )

    if not user:
        subscriber = await SubscriberDAO.find_by_lower_login(db, data.login)
        if subscriber:
            raise HTTPException(
                status_code=401,
                detail="Это не личный кабинет абонента! Авторизуйтесь на сайте lk.wifitochka.ru",
            )
        raise HTTPException(
            status_code=401,
            detail="Неправильно введён логин или пароль",
        )

    user_id = int(user["id"])
    await reset_failed_attempts(data.login)

    access_token, access_expire, access_jti = await create_token(user, token_type="access")
    refresh_token, refresh_expire, refresh_jti = await create_token(user, token_type="refresh")

    await _set_auth_cookies(
        response=response,
        access_token=access_token,
        access_expire=access_expire,
        refresh_token=refresh_token,
        refresh_expire=refresh_expire,
    )

    device_info = _get_device_info(request)

    await OssUserTokensDAO.revoke_sessions(
        db,
        filter_by={"user_id": user_id, "device_info": device_info, "is_revoked": False},
    )

    await OssUserTokensDAO.add(
        db,
        user_id=user_id,
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        ip_address=real_ip,
        user_agent=request.headers.get("user-agent"),
        device_info=device_info,
        access_expires_at=access_expire,
        refresh_expires_at=refresh_expire,
    )

    await SkystreamUsersDAO.update(db, filter_by={"id": user_id}, last_login_at=func.now())

    bg_task.add_task(_record_login_history, user_id=user_id, ip=real_ip, success=True)

    logger.info(f"User {user_id} logged in from {real_ip} | {device_info}")
    return {"success": True, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ref_token = request.cookies.get("oss_ref_token")
    if ref_token:
        payload = await decode_jwt_token(ref_token, token_type="refresh")
        refresh_jti = payload.get("jti") if payload else None
        if refresh_jti:
            await OssUserTokensDAO.revoke_sessions(
                db, filter_by={"refresh_jti": refresh_jti, "is_revoked": False}
            )

    for cookie_name in ("oss_acc_token", "oss_ref_token", "oss_login"):
        response.delete_cookie(key=cookie_name, path="/")

    return {"message": "Successfully logged out"}
