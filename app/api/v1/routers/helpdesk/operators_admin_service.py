from __future__ import annotations

import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any

import bcrypt
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth.dao import (
    HelpdeskTokensDAO,
    SkystreamUserProjectAccessDAO,
    SkystreamUsersDAO,
)
from app.api.v1.routers.helpdesk import stats_service as stats_svc
from app.config import settings
from app.constants import TRACKER_HELPDESK_LIST_SOURCES, TRACKER_OPEN_STATUSES
from app.database import get_redis

LOGIN_PATTERN = re.compile(r"^callcentre(\d+)$", re.IGNORECASE)
CYRILLIC_NAME_RE = re.compile(r"^[А-ЯЁа-яё]+(?:[ -][А-ЯЁа-яё]+)+$")

PRESENCE_PREFIX = "helpdesk:presence"
PRESENCE_TTL_SEC = 90
ACTIVITY_DB_MIN_INTERVAL_SEC = 75
OPERATORS_MANAGE_PER_PAGE_DEFAULT = 15


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


def _activity_iso(value: Any) -> str | None:
    """UTC instant в ISO 8601 с суффиксом Z для корректной конвертации на клиенте."""
    if value is None:
        return None
    dt: datetime | None
    if isinstance(value, datetime):
        dt = value
    else:
        text_val = str(value).strip()
        if not text_val:
            return None
        try:
            dt = datetime.fromisoformat(text_val.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc = dt.astimezone(timezone.utc)
    base = utc.strftime("%Y-%m-%dT%H:%M:%S")
    if utc.microsecond:
        frac = f"{utc.microsecond:06d}".rstrip("0")
        if frac:
            base = f"{base}.{frac}"
    return f"{base}Z"


async def _touch_last_activity_db(db: AsyncSession, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    try:
        row = await SkystreamUsersDAO.find_one_or_none(db, id=user_id)
        if not row:
            return
        last = row.get("last_activity")
        if last is not None:
            if isinstance(last, datetime):
                last_dt = last
            else:
                last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            if (now - last_dt).total_seconds() < ACTIVITY_DB_MIN_INTERVAL_SEC:
                return
        await SkystreamUsersDAO.update(
            db,
            filter_by={"id": user_id},
            last_activity=now,
        )
    except Exception:
        pass


async def touch_presence(db: AsyncSession, user_id: int) -> None:
    try:
        async with get_redis() as redis:
            await redis.setex(f"{PRESENCE_PREFIX}:{user_id}", PRESENCE_TTL_SEC, "1")
    except Exception:
        pass
    await _touch_last_activity_db(db, user_id)


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


def _open_helpdesk_tickets_filter_sql(*, ticket_alias: str = "tt") -> str:
    status_in = ", ".join(f"'{s}'::users.tracker_status" for s in TRACKER_OPEN_STATUSES)
    sources_in = ", ".join(f"'{s}'" for s in TRACKER_HELPDESK_LIST_SOURCES)
    return (
        f"{ticket_alias}.status IN ({status_in}) "
        f"AND COALESCE({ticket_alias}.source, 'call_center') IN ({sources_in})"
    )


async def _has_other_active_operators(db: AsyncSession, excluded_user_id: int) -> bool:
    """Есть ли другие активные операторы КС (level=1), кроме архивируемого."""
    found = (
        await db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM users.skystream_users
                    WHERE role = 'support'
                      AND level = 1
                      AND is_active = TRUE
                      AND id <> :excluded
                )
                """
            ),
            {"excluded": excluded_user_id},
        )
    ).scalar()
    return bool(found)


async def _pick_replacement_assignee(
    db: AsyncSession,
    *,
    ticket_id: int,
    excluded_user_id: int,
) -> int | None:
    """Соисполнитель тикета (приоритет) или случайный активный оператор КС (level=1)."""
    co_exec = (
        await db.execute(
            text(
                """
                SELECT tte.abs_user_id
                FROM users.tracker_ticket_executors tte
                JOIN users.skystream_users u ON u.id = tte.abs_user_id
                WHERE tte.ticket_id = :ticket_id
                  AND tte.abs_user_id <> :excluded
                  AND u.role = 'support'
                  AND u.level = 1
                  AND u.is_active = TRUE
                ORDER BY RANDOM()
                LIMIT 1
                """
            ),
            {"ticket_id": ticket_id, "excluded": excluded_user_id},
        )
    ).scalar()
    if co_exec is not None:
        return int(co_exec)

    random_op = (
        await db.execute(
            text(
                """
                SELECT id
                FROM users.skystream_users
                WHERE role = 'support'
                  AND level = 1
                  AND is_active = TRUE
                  AND id <> :excluded
                ORDER BY RANDOM()
                LIMIT 1
                """
            ),
            {"excluded": excluded_user_id},
        )
    ).scalar()
    return int(random_op) if random_op is not None else None


async def _redistribute_open_tickets_from_operator(
    db: AsyncSession,
    operator_id: int,
) -> int:
    """Переназначить открытые тикеты архивируемого оператора. Возвращает число тикетов."""
    open_filter = _open_helpdesk_tickets_filter_sql()
    if not await _has_other_active_operators(db, operator_id):
        cleared = (
            await db.execute(
                text(
                    f"""
                    UPDATE users.tracker_tickets tt
                    SET assigned_to = NULL, updated_at = NOW()
                    WHERE tt.assigned_to = :operator_id
                      AND {open_filter}
                    RETURNING tt.id
                    """
                ),
                {"operator_id": operator_id},
            )
        ).scalars().all()
        return len(cleared)

    ticket_ids = (
        await db.execute(
            text(
                f"""
                SELECT tt.id
                FROM users.tracker_tickets tt
                WHERE tt.assigned_to = :operator_id
                  AND {open_filter}
                ORDER BY tt.id
                """
            ),
            {"operator_id": operator_id},
        )
    ).scalars().all()

    for ticket_id in ticket_ids:
        tid = int(ticket_id)
        new_assignee = await _pick_replacement_assignee(
            db,
            ticket_id=tid,
            excluded_user_id=operator_id,
        )
        if new_assignee is None:
            await db.execute(
                text(
                    """
                    UPDATE users.tracker_tickets
                    SET assigned_to = NULL, updated_at = NOW()
                    WHERE id = :ticket_id
                    """
                ),
                {"ticket_id": tid},
            )
        else:
            await db.execute(
                text(
                    """
                    UPDATE users.tracker_tickets
                    SET assigned_to = :new_assignee, updated_at = NOW()
                    WHERE id = :ticket_id
                    """
                ),
                {"new_assignee": new_assignee, "ticket_id": tid},
            )
    return len(ticket_ids)


async def _remove_operator_from_ticket_executors(db: AsyncSession, operator_id: int) -> None:
    await db.execute(
        text(
            """
            DELETE FROM users.tracker_ticket_executors
            WHERE abs_user_id = :operator_id
            """
        ),
        {"operator_id": operator_id},
    )


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


def _build_manage_item(
    row: dict[str, Any],
    *,
    online: dict[int, bool],
    open_tickets: dict[int, int],
) -> dict[str, Any]:
    is_active = bool(row.get("is_active"))
    uid = int(row["id"])
    is_online = bool(online.get(uid, False))
    level = int(row["level"]) if row.get("level") is not None else None
    activity_iso = _activity_iso(row.get("last_activity"))
    return {
        "id": uid,
        "login": str(row.get("login") or ""),
        "full_name": (row.get("full_name") or "").strip() or None,
        "email": (row.get("email") or "").strip() or None,
        "is_active": is_active,
        "is_online": is_online,
        "level": level,
        "open_tickets_count": int(open_tickets.get(uid, 0)),
        "last_activity": activity_iso if is_active and not is_online and activity_iso else None,
    }


async def _fetch_operator_level_stats(db: AsyncSession) -> dict[str, int]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, is_active
                FROM users.skystream_users
                WHERE role = 'support' AND level = 1
                """
            )
        )
    ).mappings().all()
    ids = [int(r["id"]) for r in rows]
    online = await _online_map(ids)
    active_count = 0
    online_count = 0
    for row in rows:
        is_active = bool(row.get("is_active"))
        uid = int(row["id"])
        if is_active:
            active_count += 1
            if online.get(uid, False):
                online_count += 1
    return {"active_count": active_count, "online_count": online_count}


async def fetch_operators_manage(
    db: AsyncSession,
    *,
    page: int = 1,
    per_page: int = OPERATORS_MANAGE_PER_PAGE_DEFAULT,
) -> dict[str, Any]:
    page = max(1, page)
    per_page = max(1, min(int(per_page), 100))
    offset = (page - 1) * per_page

    admin_rows = (
        await db.execute(
            text(
                """
                SELECT id, login, email, full_name, is_active, level, last_activity
                FROM users.skystream_users
                WHERE role = 'support' AND level = 2
                ORDER BY COALESCE(NULLIF(TRIM(full_name), ''), login)
                """
            )
        )
    ).mappings().all()

    operator_total = int(
        (
            await db.execute(
                text(
                    """
                    SELECT COUNT(*)::int
                    FROM users.skystream_users
                    WHERE role = 'support' AND COALESCE(level, 1) <> 2
                    """
                )
            )
        ).scalar_one()
    )
    total_pages = max(1, (operator_total + per_page - 1) // per_page) if operator_total else 1
    if page > total_pages:
        page = total_pages
        offset = (page - 1) * per_page

    operator_rows = (
        await db.execute(
            text(
                """
                SELECT id, login, email, full_name, is_active, level, last_activity
                FROM users.skystream_users
                WHERE role = 'support' AND COALESCE(level, 1) <> 2
                ORDER BY is_active DESC, COALESCE(NULLIF(TRIM(full_name), ''), login)
                LIMIT :per_page OFFSET :offset
                """
            ),
            {"per_page": per_page, "offset": offset},
        )
    ).mappings().all()

    items_raw = [dict(r) for r in admin_rows] + [dict(r) for r in operator_rows]
    ids = [int(r["id"]) for r in items_raw]
    online = await _online_map(ids)
    open_tickets = await _fetch_open_ticket_counts_by_assignee(db, ids)

    admins = [
        _build_manage_item(dict(r), online=online, open_tickets=open_tickets)
        for r in admin_rows
    ]
    operators = [
        _build_manage_item(dict(r), online=online, open_tickets=open_tickets)
        for r in operator_rows
    ]
    stats = await _fetch_operator_level_stats(db)

    return {
        "admins": admins,
        "operators": operators,
        "stats": stats,
        "operators_pagination": {
            "page": page,
            "per_page": per_page,
            "total": operator_total,
            "total_pages": total_pages,
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


async def _grant_helpdesk_login_access(
    db: AsyncSession,
    *,
    user_id: int,
    granted_by: int | None = None,
) -> None:
    """Доступ к порталу helpdesk (users.skystream_user_project_access, project_id из настроек)."""
    project_id = settings.HELPDESK_SKYSTREAM_PROJECT_ID
    existing = await SkystreamUserProjectAccessDAO.find_one_or_none(
        db,
        user_id=user_id,
        project_id=project_id,
    )
    if existing:
        await SkystreamUserProjectAccessDAO.update(
            db,
            filter_by={"user_id": user_id, "project_id": project_id},
            auto_commit=False,
            can_login=True,
        )
        return
    await SkystreamUserProjectAccessDAO.add(
        db,
        auto_commit=False,
        user_id=user_id,
        project_id=project_id,
        can_login=True,
        can_admin=False,
        granted_by=granted_by,
    )


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
    await _grant_helpdesk_login_access(db, user_id=uid, granted_by=granted_by)
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
        "last_activity": None,
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

    if is_active is False:
        await _redistribute_open_tickets_from_operator(db, operator_id)
        await _remove_operator_from_ticket_executors(db, operator_id)

    await SkystreamUsersDAO.update(
        db,
        filter_by={"id": operator_id},
        auto_commit=False,
        **updates,
    )
    if is_active is False:
        await HelpdeskTokensDAO.revoke_sessions(
            db,
            filter_by={"user_id": operator_id, "is_revoked": False},
            auto_commit=False,
        )
    await db.commit()
    updated = await _get_support_operator(db, operator_id)
    online = await _online_map([operator_id])
    is_online = bool(online.get(operator_id, False))
    is_active = bool(updated.get("is_active"))
    activity_iso = _activity_iso(updated.get("last_activity"))
    return {
        "id": operator_id,
        "login": str(updated.get("login") or ""),
        "full_name": (updated.get("full_name") or "").strip() or None,
        "email": (updated.get("email") or "").strip() or None,
        "is_active": is_active,
        "is_online": is_online,
        "level": int(updated["level"]) if updated.get("level") is not None else None,
        "open_tickets_count": int(
            (await _fetch_open_ticket_counts_by_assignee(db, [operator_id])).get(operator_id, 0)
        ),
        "last_activity": activity_iso if is_active and not is_online and activity_iso else None,
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
