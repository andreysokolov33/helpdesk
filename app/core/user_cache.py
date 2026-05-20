"""
Синхронизация Redis-кэша абонента (ключ user:{id}, JSON STRING, TTL 24ч).
Совместимо с abs-flask / SubscriberService — см. temp/user_cache.txt.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import RedisCache

logger = logging.getLogger("abs")

# Общий экземпляр с префиксом user (как RedisCache(prefix="user") в abs-flask)
user_cache = RedisCache(prefix="user")

USER_CACHE_TTL = 86400


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


async def on_unarchive(session: AsyncSession, user_id: int) -> None:
    """Разархивация: patch is_archive, user_status, status (abs pays/archive flow)."""
    await sync_user_cache_from_db(session, user_id)


async def on_tariff_freeze_changed(session: AsyncSession, user_id: int) -> None:
    """
    Заморозка / разморозка / отмена плана: delete + при наличии кэша можно patch статуса из БД.
    abs-flask: delete; дополнительно синхронизируем статус, если ключ ещё не удалили конкурентно.
    """
    await sync_user_cache_from_db(session, user_id)
    await invalidate_user_cache(user_id)
