from __future__ import annotations

import re
import secrets
import string
from typing import Any

import bcrypt
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth.dao import SkystreamUserProjectAccessDAO, SkystreamUsersDAO
from app.api.v1.routers.helpdesk import stats_service as stats_svc
from app.config import settings
from app.constants import TRACKER_HELPDESK_LIST_SOURCES, TRACKER_OPEN_STATUSES
from app.database import get_redis

LOGIN_PATTERN = re.compile(r"^callcentre(\d+)$", re.IGNORECASE)
CYRILLIC_NAME_RE = re.compile(r"^[А-ЯЁа-яё]+(?:[ -][А-ЯЁа-яё]+)+$")

PRESENCE_PREFIX = "helpdesk:presence"
PRESENCE_TTL_SEC = 90


def generate_operator_password(length: int = 10) -> str:
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    pool = lowers + uppers + digits
    rng = secrets.SystemRandom()
    chars = [rng.choice(lowers), rng.choice(uppers), rng.choice(digits)]
    chars += [rng.choice(pool) for _ in range(length - 3)]
    rng.shuffle(chars)
    return "".join(chars)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_password(password: str) -> None:
    if len(password) != 10:
        raise HTTPException(status_code=400, detail="Пароль должен содержать 10 символов")
    allowed = set(string.ascii_letters + string.digits)
    if not all(c in allowed for c in password):
        raise HTTPException(status_code=400, detail="Пароль: только латинские буквы и цифры")
    if not any(c.islower() for c in password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать строчные буквы")
    if not any(c.isupper() for c in password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать заглавные буквы")
    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать цифры")


def validate_full_name(full_name: str) -> str:
    name = full_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Укажите ФИО")
    if not CYRILLIC_NAME_RE.fullmatch(name):
        raise HTTPException(
            status_code=400,
            detail="ФИО: только русские буквы, минимум имя и фамилия",
        )
    return name


async def _viewer_is_admin(db: AsyncSession, user: dict[str, Any]) -> bool:
    uid = int(user["user_id"])
    role = user.get("role")
    level = user.get("level")
    if level is None:
        row = await SkystreamUsersDAO.find_one_or_none(db, id=uid)
        if row:
            role = role or row.get("role")
            lvl = row.get("level")
            level = int(lvl) if lvl is not None else None
    lvl_int = int(level) if level is not None else None
    return stats_svc.is_support_admin(role=role, level=lvl_int)


async def require_support_admin(db: AsyncSession, user: dict[str, Any]) -> None:
    if not await _viewer_is_admin(db, user):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


async def touch_presence(user_id: int) -> None:
    try:
        async with get_redis() as redis:
            await redis.setex(f"{PRESENCE_PREFIX}:{user_id}", PRESENCE_TTL_SEC, "1")
    except Exception:
        pass


async def _online_map(user_ids: list[int]) -> dict[int, bool]:
    if not user_ids:
        return {}
    keys = [f"{PRESENCE_PREFIX}:{uid}" for uid in user_ids]
    try:
        async with get_redis() as redis:
            flags = await redis.mget(keys)
        if not flags:
            return {uid: False for uid in user_ids}
    except Exception:
        return {uid: False for uid in user_ids}
    return {
        uid: bool(raw)
        for uid, raw in zip(user_ids, flags, strict=True)
    }


async def _fetch_open_ticket_counts_by_assignee(
    db: AsyncSession,
    user_ids: list[int],
) -> dict[int, int]:
    if not user_ids:
        return {}
    status_in = ", ".join(f"'{s}'::users.tracker_status" for s in TRACKER_OPEN_STATUSES)
    sources_in = ", ".join(f"'{s}'" for s in TRACKER_HELPDESK_LIST_SOURCES)
    rows = (
        await db.execute(
            text(
                f"""
                SELECT tt.assigned_to AS user_id, COUNT(*)::int AS cnt
                FROM users.tracker_tickets tt
                WHERE tt.assigned_to = ANY(:user_ids)
                  AND tt.status IN ({status_in})
                  AND COALESCE(tt.source, 'call_center') IN ({sources_in})
                GROUP BY tt.assigned_to
                """
            ),
            {"user_ids": user_ids},
        )
    ).mappings().all()
    return {int(r["user_id"]): int(r["cnt"]) for r in rows}


async def fetch_suggested_login(db: AsyncSession) -> str:
    rows = (
        await db.execute(
            text(
                """
                SELECT login
                FROM users.skystream_users
                WHERE login ~* '^callcentre[0-9]+$'
                """
            )
        )
    ).scalars().all()
    max_n = 0
    for login in rows:
        m = LOGIN_PATTERN.match(str(login or ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"callcentre{max_n + 1}"


async def fetch_operators_manage(db: AsyncSession) -> dict[str, Any]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, login, email, full_name, is_active, level
                FROM users.skystream_users
                WHERE role = 'support'
                ORDER BY is_active DESC, COALESCE(NULLIF(TRIM(full_name), ''), login)
                """
            )
        )
    ).mappings().all()
    items_raw = [dict(r) for r in rows]
    ids = [int(r["id"]) for r in items_raw]
    online = await _online_map(ids)
    open_tickets = await _fetch_open_ticket_counts_by_assignee(db, ids)

    admins: list[dict[str, Any]] = []
    operators: list[dict[str, Any]] = []
    active_count = 0
    online_count = 0
    for row in items_raw:
        is_active = bool(row.get("is_active"))
        is_online = bool(online.get(int(row["id"]), False))
        level = int(row["level"]) if row.get("level") is not None else None
        uid = int(row["id"])
        item = {
            "id": uid,
            "login": str(row.get("login") or ""),
            "full_name": (row.get("full_name") or "").strip() or None,
            "email": (row.get("email") or "").strip() or None,
            "is_active": is_active,
            "is_online": is_online,
            "level": level,
            "open_tickets_count": int(open_tickets.get(uid, 0)),
        }
        if level == 2:
            admins.append(item)
        else:
            operators.append(item)
        if level == 1:
            if is_active:
                active_count += 1
            if is_active and is_online:
                online_count += 1

    return {
        "admins": admins,
        "operators": operators,
        "stats": {
            "active_count": active_count,
            "online_count": online_count,
        },
    }


async def _get_support_operator(db: AsyncSession, operator_id: int) -> dict[str, Any]:
    row = await SkystreamUsersDAO.find_one_or_none(db, id=operator_id)
    if not row or row.get("role") != "support":
        raise HTTPException(status_code=404, detail="Оператор не найден")
    return row


def _assert_can_manage_operator(*, viewer_id: int, target: dict[str, Any]) -> None:
    target_id = int(target["id"])
    level = target.get("level")
    if level == 2 and target_id != viewer_id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать другого администратора")


async def create_operator(
    db: AsyncSession,
    *,
    login: str,
    password: str,
    full_name: str,
    email: str | None,
    granted_by: int,
) -> dict[str, Any]:
    login_clean = login.strip()
    if not login_clean:
        raise HTTPException(status_code=400, detail="Укажите логин")
    if await SkystreamUsersDAO.find_by_lower_login(db, login=login_clean):
        raise HTTPException(status_code=409, detail="Логин уже занят")

    validate_password(password)
    name = validate_full_name(full_name)
    email_val = email.strip() if email and email.strip() else None

    user = await SkystreamUsersDAO.add(
        db,
        auto_commit=False,
        login=login_clean,
        email=email_val,
        full_name=name,
        password_hash=hash_password(password),
        role="support",
        is_superuser=False,
        is_active=True,
        level=1,
    )
    uid = int(user["id"])
    await SkystreamUserProjectAccessDAO.add(
        db,
        auto_commit=False,
        user_id=uid,
        project_id=settings.HELPDESK_SKYSTREAM_PROJECT_ID,
        can_login=True,
        can_admin=False,
        granted_by=granted_by,
    )
    await db.commit()
    return {
        "id": uid,
        "login": login_clean,
        "full_name": name,
        "email": email_val,
        "is_active": True,
        "is_online": False,
        "level": 1,
        "open_tickets_count": 0,
    }


async def update_operator(
    db: AsyncSession,
    *,
    operator_id: int,
    viewer_id: int,
    full_name: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    row = await _get_support_operator(db, operator_id)
    _assert_can_manage_operator(viewer_id=viewer_id, target=row)
    if int(row["id"]) == viewer_id and is_active is False:
        raise HTTPException(status_code=400, detail="Нельзя архивировать свой аккаунт")
    if row.get("level") == 2 and is_active is False and int(row["id"]) != viewer_id:
        raise HTTPException(status_code=400, detail="Нельзя архивировать администратора")

    updates: dict[str, Any] = {}
    if full_name is not None:
        updates["full_name"] = validate_full_name(full_name)
    if is_active is not None:
        updates["is_active"] = is_active
    if not updates:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    await SkystreamUsersDAO.update(db, filter_by={"id": operator_id}, **updates)
    updated = await _get_support_operator(db, operator_id)
    online = await _online_map([operator_id])
    return {
        "id": operator_id,
        "login": str(updated.get("login") or ""),
        "full_name": (updated.get("full_name") or "").strip() or None,
        "email": (updated.get("email") or "").strip() or None,
        "is_active": bool(updated.get("is_active")),
        "is_online": bool(online.get(operator_id, False)),
        "level": int(updated["level"]) if updated.get("level") is not None else None,
        "open_tickets_count": int(
            (await _fetch_open_ticket_counts_by_assignee(db, [operator_id])).get(operator_id, 0)
        ),
    }


async def reset_operator_password(
    db: AsyncSession,
    *,
    operator_id: int,
    viewer_id: int,
    password: str,
) -> None:
    row = await _get_support_operator(db, operator_id)
    _assert_can_manage_operator(viewer_id=viewer_id, target=row)
    validate_password(password)
    await SkystreamUsersDAO.update(
        db,
        filter_by={"id": operator_id},
        password_hash=hash_password(password),
    )
