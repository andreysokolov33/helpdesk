"""
Синхронизация Redis-кэша абонента (ключ user:{id}, JSON STRING, TTL 24ч).
Совместимо с abs-flask / SubscriberService — см. temp/user_cache.txt.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import RedisCache
from app.database import redis_client

logger = logging.getLogger("abs")

# Общий экземпляр с префиксом user (как RedisCache(prefix="user") в abs-flask)
user_cache = RedisCache(prefix="user")

USER_CACHE_TTL = 86400

# Успешные сбросы сессий (helpdesk «Закрыть сессии») — не чаще N раз за окно.
DISCONNECT_SESSIONS_MAX = 2
DISCONNECT_SESSIONS_WINDOW_SEC = 30 * 60
_DISCONNECT_TS_FIELD = "disconnect_sessions_ts"


def disconnect_sessions_limit_exceeded_message() -> str:
    minutes = max(1, DISCONNECT_SESSIONS_WINDOW_SEC // 60)
    return (
        f"Лимит сброса сессий исчерпан ({DISCONNECT_SESSIONS_MAX} раза за {minutes} мин.). "
        "Повторите позже."
    )


def status_from_user_status(user_status: Optional[int]) -> str:
    """
    users.user.user_status → поле status в кэше.
    1 (и прочие кроме 2/3) → active; 2 → frozen; 3 → archived.
    """
    us = int(user_status if user_status is not None else 1)
    if us == 3:
        return "archived"
    if us == 2:
        return "frozen"
    return "active"


def status_fields_from_user_row(user_row: dict[str, Any]) -> dict[str, Any]:
    """Поля is_archive, user_status, status для patch кэша из строки users.user."""
    us = int(user_row.get("user_status") if user_row.get("user_status") is not None else 1)
    arch = int(user_row.get("archive") or 0)
    return {
        "user_status": us,
        "status": status_from_user_status(us),
        "is_archive": bool(arch),
    }


async def patch_user_cache(user_id: int, updates: dict[str, Any]) -> bool:
    """Точечное обновление JSON в user:{id}. False — ключа нет."""
    ok = await user_cache.patch(user_id, updates, ttl=USER_CACHE_TTL)
    if ok:
        logger.debug("Patched user cache %s: %s", user_id, list(updates.keys()))
    return ok


async def invalidate_user_cache(user_id: int) -> None:
    """Полный сброс ключа (freeze/unfreeze, reset-cache и т.п.)."""
    await user_cache.delete(user_id)
    logger.debug("Invalidated user cache %s", user_id)


async def sync_user_cache_from_db(session: AsyncSession, user_id: int) -> bool:
    """Подтянуть user_status / status / is_archive из БД в существующий кэш."""
    from app.api.v1.routers.users.dao import UsersDAO

    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        return False
    return await patch_user_cache(user_id, status_fields_from_user_row(row))


def _prune_disconnect_timestamps(timestamps: list[Any], now: int) -> list[int]:
    cutoff = now - DISCONNECT_SESSIONS_WINDOW_SEC
    out: list[int] = []
    for t in timestamps:
        try:
            ts = int(t)
        except (TypeError, ValueError):
            continue
        if ts > cutoff:
            out.append(ts)
    return out


async def _load_disconnect_timestamps(user_id: int) -> list[int]:
    cached = await user_cache.get(user_id)
    if cached and _DISCONNECT_TS_FIELD in cached:
        return _prune_disconnect_timestamps(cached.get(_DISCONNECT_TS_FIELD) or [], int(time.time()))
    raw = await redis_client.get(f"user:{user_id}:disconnect_sessions")
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return _prune_disconnect_timestamps(data.get("ts") or [], int(time.time()))
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


async def _save_disconnect_timestamps(user_id: int, timestamps: list[int]) -> None:
    if await user_cache.patch(user_id, {_DISCONNECT_TS_FIELD: timestamps}, ttl=USER_CACHE_TTL):
        return
    await redis_client.set(
        f"user:{user_id}:disconnect_sessions",
        json.dumps({"ts": timestamps}, ensure_ascii=False),
        ex=DISCONNECT_SESSIONS_WINDOW_SEC,
    )


async def get_disconnect_sessions_remaining(user_id: int) -> tuple[int, int]:
    """(использовано за окно, осталось попыток)."""
    active = await _load_disconnect_timestamps(user_id)
    used = len(active)
    return used, max(0, DISCONNECT_SESSIONS_MAX - used)


async def check_disconnect_sessions_allowed(user_id: int) -> tuple[bool, Optional[str]]:
    _, remaining = await get_disconnect_sessions_remaining(user_id)
    if remaining <= 0:
        return False, disconnect_sessions_limit_exceeded_message()
    return True, None


async def record_disconnect_sessions_success(user_id: int) -> None:
    now = int(time.time())
    active = await _load_disconnect_timestamps(user_id)
    active.append(now)
    active = _prune_disconnect_timestamps(active, now)
    await _save_disconnect_timestamps(user_id, active)


async def on_unarchive(session: AsyncSession, user_id: int) -> None:
    """Разархивация: is_archive, user_status, status в user:{id} (как abs-flask pays/archive)."""
    from app.api.v1.routers.users.dao import UsersDAO

    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        return
    fields = status_fields_from_user_row(row)
    cached = await user_cache.get(user_id)
    if cached:
        cached.update(fields)
        await user_cache.set(user_id, cached, ttl=USER_CACHE_TTL)
        logger.debug("Unarchive: patched user cache %s", user_id)
    else:
        await sync_user_cache_from_db(session, user_id)


async def on_tariff_freeze_changed(session: AsyncSession, user_id: int) -> None:
    """
    Заморозка / разморозка / отмена плана: delete + при наличии кэша можно patch статуса из БД.
    abs-flask: delete; дополнительно синхронизируем статус, если ключ ещё не удалили конкурентно.
    """
    await sync_user_cache_from_db(session, user_id)
    await invalidate_user_cache(user_id)
