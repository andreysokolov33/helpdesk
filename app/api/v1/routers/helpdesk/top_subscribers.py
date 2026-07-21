"""ТОП абонентов по платежам (monitoring.top_history, stat_id=4)."""

from __future__ import annotations

from typing import Any, Iterable, MutableMapping, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Категория: скользящая средняя по платежам (см. monitoring.top_history_category)
TOP_HISTORY_STAT_PAYMENTS = 4


async def fetch_top_rank_map(
    db: AsyncSession,
    uids: Iterable[int],
    *,
    stat_id: int = TOP_HISTORY_STAT_PAYMENTS,
) -> dict[int, int]:
    """uid → rank по последнему snapshot_date для категории."""
    ids = sorted({int(u) for u in uids if u is not None})
    if not ids:
        return {}
    rows = (
        await db.execute(
            text(
                """
                SELECT th.uid, th.rank
                FROM monitoring.top_history th
                WHERE th.stat_id = :stat_id
                  AND th.uid = ANY(:uids)
                  AND th.snapshot_date = (
                      SELECT MAX(snapshot_date)
                      FROM monitoring.top_history
                      WHERE stat_id = :stat_id
                  )
                """
            ),
            {"stat_id": stat_id, "uids": ids},
        )
    ).mappings().all()
    out: dict[int, int] = {}
    for r in rows:
        uid, rank = r.get("uid"), r.get("rank")
        if uid is None or rank is None:
            continue
        try:
            out[int(uid)] = int(rank)
        except (TypeError, ValueError):
            continue
    return out


async def fetch_top_subscriber_rank(
    db: AsyncSession,
    uid: Optional[int],
    *,
    stat_id: int = TOP_HISTORY_STAT_PAYMENTS,
) -> Optional[int]:
    if uid is None:
        return None
    return (await fetch_top_rank_map(db, [int(uid)], stat_id=stat_id)).get(int(uid))


async def enrich_rows_with_top_rank(
    db: AsyncSession,
    rows: list[MutableMapping[str, Any]],
    *,
    uid_key: str = "user_id",
    out_key: str = "top_subscriber_rank",
    stat_id: int = TOP_HISTORY_STAT_PAYMENTS,
) -> None:
    """Проставляет out_key из top_history; иначе None."""
    if not rows:
        return
    uids: list[int] = []
    for row in rows:
        raw = row.get(uid_key)
        if raw is None and uid_key == "user_id":
            raw = row.get("chat_id")
        if raw is not None:
            try:
                uids.append(int(raw))
            except (TypeError, ValueError):
                pass
    rank_map = await fetch_top_rank_map(db, uids, stat_id=stat_id)
    for row in rows:
        raw = row.get(uid_key)
        if raw is None and uid_key == "user_id":
            raw = row.get("chat_id")
        try:
            uid = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            uid = None
        row[out_key] = rank_map.get(uid) if uid is not None else None


async def enrich_chats_with_top_rank(
    db: AsyncSession,
    chats: list[MutableMapping[str, Any]],
) -> None:
    await enrich_rows_with_top_rank(db, chats, uid_key="chat_id")
