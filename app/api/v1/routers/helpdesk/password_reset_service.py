from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.operator_log_service import write_operator_log
from app.api.v1.routers.helpdesk.password_reset_schemas import (
    PasswordResetGenerateResponse,
    PasswordResetPollResponse,
    PasswordResetStateResponse,
)
from app.api.v1.routers.users.dao import UsersDAO
from app.core.redis import RedisCache
from app.models.users import PasswordResetCode

CODE_TTL_MINUTES = 10
_pwd_reset_display = RedisCache(prefix="helpdesk_pwd_reset_display")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(code: str, salt: str) -> str:
    return hashlib.sha256(f"{code}:{salt}".encode("utf-8")).hexdigest()


def _gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _gen_salt() -> str:
    return secrets.token_hex(16)


async def _has_ppp_sessions(session: AsyncSession, login: str) -> bool:
    if not login.strip():
        return False
    row = (
        await session.execute(
            text("""
                SELECT 1
                FROM radius.radacct r
                WHERE lower(r.username) = lower(:login)
                  AND r.framedprotocol = 'PPP'
                ORDER BY r.acctstoptime DESC NULLS LAST
                LIMIT 1
            """),
            {"login": login.strip()},
        )
    ).first()
    return row is not None


async def _deactivate_code(
    session: AsyncSession,
    code_id: int,
    reason: str,
) -> None:
    await session.execute(
        update(PasswordResetCode)
        .where(PasswordResetCode.id == code_id)
        .values(
            is_active=False,
            deactivation_reason=reason,
            deactivated_at=_utcnow(),
        )
    )


async def _get_active_code_row(session: AsyncSession, user_id: int) -> Optional[PasswordResetCode]:
    now = _utcnow()
    result = await session.execute(
        select(PasswordResetCode)
        .where(
            PasswordResetCode.user_id == user_id,
            PasswordResetCode.is_active.is_(True),
            PasswordResetCode.used_at.is_(None),
        )
        .order_by(PasswordResetCode.id.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    if row.expires_at <= now:
        await _deactivate_code(session, int(row.id), "expired")
        await _pwd_reset_display.delete(str(user_id))
        return None
    return row


async def _cache_display_code(user_id: int, code: str, code_id: int, expires_at: datetime) -> None:
    ttl = max(1, int((expires_at - _utcnow()).total_seconds()))
    await _pwd_reset_display.set(
        str(user_id),
        {"code": code, "code_id": code_id, "expires_at": expires_at.isoformat()},
        ttl=ttl,
    )


async def _read_display_code(user_id: int, code_id: int) -> Optional[str]:
    cached = await _pwd_reset_display.get(str(user_id))
    if not cached or cached.get("code_id") != code_id:
        return None
    return str(cached.get("code") or "")


async def get_password_reset_state(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> PasswordResetStateResponse:
    u = await UsersDAO.find_one_or_none(session, id=user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Абонент не найден")

    login = (u.get("login") or "").strip()
    has_ppp = await _has_ppp_sessions(session, login)

    await write_operator_log(
        session,
        operator_id=int(operator["user_id"]),
        action="password_reset.modal_open",
        subscriber_id=user_id,
        page=f"/users/{user_id}",
        request=request,
        details={"has_ppp_sessions": has_ppp},
        auto_commit=False,
    )

    active = await _get_active_code_row(session, user_id)
    if not active:
        await session.commit()
        return PasswordResetStateResponse(
            has_ppp_sessions=has_ppp,
            can_generate=True,
        )

    display = await _read_display_code(user_id, int(active.id))
    await session.commit()
    return PasswordResetStateResponse(
        has_ppp_sessions=has_ppp,
        active_code=display or None,
        expires_at=active.expires_at,
        can_generate=display is None,
        code_id=int(active.id),
    )


async def generate_password_reset_code(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> PasswordResetGenerateResponse:
    u = await UsersDAO.find_one_or_none(session, id=user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Абонент не найден")

    active = await _get_active_code_row(session, user_id)
    if active:
        display = await _read_display_code(user_id, int(active.id))
        if display:
            await session.commit()
            return PasswordResetGenerateResponse(
                code=display,
                expires_at=active.expires_at,
                code_id=int(active.id),
                message="Действующий код ещё активен",
            )
        await _deactivate_code(session, int(active.id), "superseded")

    now = _utcnow()
    expires_at = now + timedelta(minutes=CODE_TTL_MINUTES)
    code = _gen_code()
    salt = _gen_salt()
    code_hash = _hash_code(code, salt)

    prev_rows = (
        await session.execute(
            select(PasswordResetCode.id).where(
                PasswordResetCode.user_id == user_id,
                PasswordResetCode.is_active.is_(True),
                PasswordResetCode.used_at.is_(None),
            )
        )
    ).scalars().all()
    for pid in prev_rows:
        await _deactivate_code(session, int(pid), "superseded")

    row = PasswordResetCode(
        user_id=user_id,
        operator_id=int(operator["user_id"]),
        code_hash=code_hash,
        code_salt=salt,
        expires_at=expires_at,
        is_active=True,
    )
    session.add(row)
    await session.flush()

    await _cache_display_code(user_id, code, int(row.id), expires_at)

    await write_operator_log(
        session,
        operator_id=int(operator["user_id"]),
        action="password_reset.generate",
        subscriber_id=user_id,
        page=f"/users/{user_id}",
        request=request,
        password_reset_code_id=int(row.id),
        details={
            "expires_at": expires_at.isoformat(),
            "ttl_minutes": CODE_TTL_MINUTES,
        },
        auto_commit=False,
    )

    await session.commit()
    return PasswordResetGenerateResponse(code=code, expires_at=expires_at, code_id=int(row.id))


async def poll_password_reset_status(
    session: AsyncSession,
    user_id: int,
    code_id: Optional[int] = None,
) -> PasswordResetPollResponse:
    """Статус кода для поллинга в модалке оператора (без записи в лог)."""
    row: Optional[PasswordResetCode] = None
    if code_id is not None:
        result = await session.execute(
            select(PasswordResetCode).where(
                PasswordResetCode.id == code_id,
                PasswordResetCode.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
    else:
        row = await _get_active_code_row(session, user_id)

    if not row:
        return PasswordResetPollResponse()

    if row.used_at is not None:
        return PasswordResetPollResponse(code_used=True, code_id=int(row.id))

    now = _utcnow()
    if not row.is_active or row.expires_at <= now:
        if row.expires_at <= now and row.used_at is None:
            await _deactivate_code(session, int(row.id), "expired")
            await _pwd_reset_display.delete(str(user_id))
            await session.commit()
        return PasswordResetPollResponse(code_expired=True, code_id=int(row.id))

    display = await _read_display_code(user_id, int(row.id))
    return PasswordResetPollResponse(
        active_code=display,
        expires_at=row.expires_at,
        code_id=int(row.id),
    )
