"""Данные для главной страницы оператора КС."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.ticket_service import _support_co_executor_exists_sql
from app.database import redis_client

_RATINGS_DIGEST_CACHE_TTL = 8


def _home_ratings_viewer_scope_sql(*, alias: str = "tt", user_param: str = ":viewer_id") -> str:
    co_exec = _support_co_executor_exists_sql(ticket_expr=f"{alias}.id", user_param=user_param)
    return f"""(
        {alias}.assigned_to = {user_param}
        OR {co_exec}
        OR {alias}.engineer_id = {user_param}
    )"""


def _ratings_digest_cache_key(viewer_id: int) -> str:
    return f"home_ratings_digest:{viewer_id}"


async def fetch_home_recent_ratings(
    db: AsyncSession,
    *,
    viewer_id: int,
    limit: int = 5,
) -> list[dict[str, Any]]:
    scope = _home_ratings_viewer_scope_sql()
    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    tt.id AS ticket_id,
                    ttr.rating,
                    ttr.comment AS rating_comment,
                    ttr.date AS rated_at,
                    u.login AS subscriber_login,
                    u.is_juridical AS sub_is_juridical,
                    ud.surname AS ud_surname,
                    ud.name AS ud_name,
                    ud.patronymic AS ud_patronymic,
                    jur.short_name_organization AS jur_short_name
                FROM users.tracker_tickets_ratings ttr
                JOIN users.tracker_tickets tt ON tt.id = ttr.ticket_id
                LEFT JOIN users."user" u ON tt.user_id = u.id AND tt.object_type = 'user'
                LEFT JOIN LATERAL (
                    SELECT ud.surname, ud.name, ud.patronymic
                    FROM users.user_details ud
                    WHERE ud.user_id = u.id AND ud.is_actual IS TRUE
                    ORDER BY ud.id DESC
                    LIMIT 1
                ) ud ON TRUE
                LEFT JOIN oss.jur_client_list jur ON jur.id = u.juridical_id
                WHERE {scope}
                ORDER BY ttr.date DESC NULLS LAST, tt.id DESC
                LIMIT :limit
                """
            ),
            {"viewer_id": viewer_id, "limit": limit},
        )
    ).mappings().all()

    out: list[dict[str, Any]] = []
    for r in rows:
        ij = int(r.get("sub_is_juridical") or 0)
        login = (r.get("subscriber_login") or "").strip()
        if ij == 2:
            name = (r.get("jur_short_name") or "").strip() or login or f"#{r['ticket_id']}"
        else:
            parts = [
                (r.get("ud_surname") or "").strip(),
                (r.get("ud_name") or "").strip(),
                (r.get("ud_patronymic") or "").strip(),
            ]
            fio = " ".join(p for p in parts if p)
            name = fio or login or f"Тикет #{r['ticket_id']}"
        rated_at = r.get("rated_at")
        out.append(
            {
                "ticket_id": int(r["ticket_id"]),
                "rating": int(r["rating"]),
                "rating_comment": (r.get("rating_comment") or "").strip() or None,
                "rated_at": rated_at.isoformat() if rated_at is not None else None,
                "subscriber_name": name,
            }
        )
    return out


def _ratings_digest_from_rows(rows: list[dict[str, Any]]) -> str:
    parts = [
        f"{r['ticket_id']}|{r['rating']}|{r.get('rated_at') or ''}"
        for r in rows
    ]
    raw = ",".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()


async def fetch_home_ratings_digest(
    db: AsyncSession,
    *,
    viewer_id: int,
    client_digest: str | None = None,
) -> dict[str, Any]:
    cache_key = _ratings_digest_cache_key(viewer_id)
    try:
        cached_raw = await redis_client.get(cache_key)
        if cached_raw:
            cached = json.loads(cached_raw)
            if isinstance(cached, dict) and cached.get("digest"):
                digest = str(cached["digest"])
                count = int(cached.get("count") or 0)
                changed = not client_digest or client_digest != digest
                return {"changed": changed, "digest": digest, "count": count}
    except Exception:
        pass

    rows = await fetch_home_recent_ratings(db, viewer_id=viewer_id, limit=5)
    digest = _ratings_digest_from_rows(rows)
    count = len(rows)
    try:
        await redis_client.setex(
            cache_key,
            _RATINGS_DIGEST_CACHE_TTL,
            json.dumps({"digest": digest, "count": count}),
        )
    except Exception:
        pass
    changed = not client_digest or client_digest != digest
    return {"changed": changed, "digest": digest, "count": count}
