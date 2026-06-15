"""Новости операторов helpdesk — колокольчик и главная."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import redis_client

_NEWS_SCHEMA = "notification"
_T_NEWS = f"{_NEWS_SCHEMA}.helpdesk_operator_news"
_T_NEWS_READ = f"{_NEWS_SCHEMA}.helpdesk_operator_news_read"

_BELL_DIGEST_CACHE_TTL = 8
_BELL_LIST_LIMIT = 30
_BELL_UNREAD_MAX_AGE_DAYS = 14

_VISIBLE_NEWS_SQL = """
    n.is_active IS TRUE
    AND n.published_at <= NOW()
    AND (n.expires_at IS NULL OR n.expires_at > NOW())
"""

def _history_access_sql() -> str:
    return f"""
    n.published_at <= NOW()
    AND (
        ({_VISIBLE_NEWS_SQL.strip()})
        OR EXISTS (
            SELECT 1
            FROM {_T_NEWS_READ} r
            WHERE r.news_id = n.id
              AND r.operator_id = :operator_id
        )
    )
"""

_UNREAD_NEWS_SQL = f"""
    {_VISIBLE_NEWS_SQL}
    AND NOT EXISTS (
        SELECT 1
        FROM {_T_NEWS_READ} r
        WHERE r.news_id = n.id
          AND r.operator_id = :operator_id
    )
"""

# В колокольчике — только непрочитанные не старше 14 суток (на /news остаются «Новое»).
_BELL_UNREAD_NEWS_SQL = f"""
    {_UNREAD_NEWS_SQL}
    AND n.published_at > NOW() - INTERVAL '{_BELL_UNREAD_MAX_AGE_DAYS} days'
"""


def _bell_digest_cache_key(operator_id: int) -> str:
    return f"helpdesk_news_bell_digest:{operator_id}"


async def fetch_operator_news_bell(
    db: AsyncSession,
    *,
    operator_id: int,
    limit: int = _BELL_LIST_LIMIT,
) -> dict[str, Any]:
    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    n.id,
                    n.title,
                    n.kind::text AS kind,
                    n.importance::text AS importance,
                    n.link_path,
                    n.published_at
                FROM {_T_NEWS} n
                WHERE {_BELL_UNREAD_NEWS_SQL}
                ORDER BY n.published_at DESC, n.id DESC
                LIMIT :limit
                """
            ),
            {"operator_id": operator_id, "limit": limit},
        )
    ).mappings().all()

    items = [
        {
            "id": int(r["id"]),
            "title": str(r["title"]),
            "kind": str(r["kind"]),
            "importance": str(r["importance"]),
            "link_path": r.get("link_path"),
            "published_at": r["published_at"],
        }
        for r in rows
    ]
    count_row = (
        await db.execute(
            text(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM {_T_NEWS} n
                WHERE {_BELL_UNREAD_NEWS_SQL}
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().one()
    return {"unread_count": int(count_row["cnt"]), "items": items}


async def fetch_operator_news_bell_digest(
    db: AsyncSession,
    *,
    operator_id: int,
    client_digest: Optional[str],
) -> dict[str, Any]:
    cache_key = _bell_digest_cache_key(operator_id)
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            if isinstance(data, dict) and "digest" in data:
                digest = str(data["digest"])
                unread_count = int(data.get("unread_count", 0))
                if client_digest and client_digest == digest:
                    return {"changed": False, "digest": digest, "unread_count": unread_count}
    except Exception:
        pass

    rows = (
        await db.execute(
            text(
                f"""
                SELECT n.id
                FROM {_T_NEWS} n
                WHERE {_BELL_UNREAD_NEWS_SQL}
                ORDER BY n.id
                """
            ),
            {"operator_id": operator_id},
        )
    ).scalars().all()
    unread_count = len(rows)
    digest_src = ",".join(str(i) for i in rows) if rows else "0"
    digest = hashlib.sha256(digest_src.encode()).hexdigest()[:16]

    try:
        await redis_client.setex(
            cache_key,
            _BELL_DIGEST_CACHE_TTL,
            json.dumps({"digest": digest, "unread_count": unread_count}),
        )
    except Exception:
        pass

    changed = not client_digest or client_digest != digest
    return {"changed": changed, "digest": digest, "unread_count": unread_count}


async def fetch_operator_news_history(
    db: AsyncSession,
    *,
    operator_id: int,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    history_sql = _history_access_sql()
    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    n.id,
                    n.title,
                    n.kind::text AS kind,
                    n.importance::text AS importance,
                    n.link_path,
                    n.published_at,
                    EXISTS (
                        SELECT 1
                        FROM {_T_NEWS_READ} r
                        WHERE r.news_id = n.id
                          AND r.operator_id = :operator_id
                    ) AS is_read,
                    (
                        SELECT r.read_at
                        FROM {_T_NEWS_READ} r
                        WHERE r.news_id = n.id
                          AND r.operator_id = :operator_id
                        LIMIT 1
                    ) AS read_at
                FROM {_T_NEWS} n
                WHERE {history_sql}
                ORDER BY n.published_at DESC, n.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"operator_id": operator_id, "limit": limit, "offset": offset},
        )
    ).mappings().all()

    count_row = (
        await db.execute(
            text(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM {_T_NEWS} n
                WHERE {history_sql}
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().one()

    unread_row = (
        await db.execute(
            text(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM {_T_NEWS} n
                WHERE {history_sql}
                  AND NOT EXISTS (
                      SELECT 1
                      FROM {_T_NEWS_READ} r
                      WHERE r.news_id = n.id
                        AND r.operator_id = :operator_id
                  )
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().one()

    items = [
        {
            "id": int(r["id"]),
            "title": str(r["title"]),
            "kind": str(r["kind"]),
            "importance": str(r["importance"]),
            "link_path": r.get("link_path"),
            "published_at": r["published_at"],
            "is_read": bool(r["is_read"]),
            "read_at": r.get("read_at"),
        }
        for r in rows
    ]
    return {
        "total": int(count_row["cnt"]),
        "unread_total": int(unread_row["cnt"]),
        "items": items,
    }


async def fetch_operator_news_detail(
    db: AsyncSession,
    *,
    operator_id: int,
    news_id: int,
) -> Optional[dict[str, Any]]:
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    n.id,
                    n.title,
                    n.body_html,
                    n.kind::text AS kind,
                    n.importance::text AS importance,
                    n.link_path,
                    n.published_at,
                    EXISTS (
                        SELECT 1
                        FROM {_T_NEWS_READ} r
                        WHERE r.news_id = n.id
                          AND r.operator_id = :operator_id
                    ) AS is_read
                FROM {_T_NEWS} n
                WHERE n.id = :news_id
                  AND {_history_access_sql()}
                """
            ),
            {"operator_id": operator_id, "news_id": news_id},
        )
    ).mappings().first()
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "body_html": str(row["body_html"] or ""),
        "kind": str(row["kind"]),
        "importance": str(row["importance"]),
        "link_path": row.get("link_path"),
        "published_at": row["published_at"],
        "is_read": bool(row["is_read"]),
    }


async def mark_operator_news_read(
    db: AsyncSession,
    *,
    operator_id: int,
    news_id: int,
) -> bool:
    visible = (
        await db.execute(
            text(
                f"""
                SELECT 1
                FROM {_T_NEWS} n
                WHERE n.id = :news_id
                  AND {_VISIBLE_NEWS_SQL}
                """
            ),
            {"news_id": news_id},
        )
    ).first()
    if not visible:
        return False

    await db.execute(
        text(
            f"""
            INSERT INTO {_T_NEWS_READ} (news_id, operator_id)
            VALUES (:news_id, :operator_id)
            ON CONFLICT (news_id, operator_id) DO NOTHING
            """
        ),
        {"news_id": news_id, "operator_id": operator_id},
    )
    await db.commit()

    try:
        await redis_client.delete(_bell_digest_cache_key(operator_id))
    except Exception:
        pass
    return True
