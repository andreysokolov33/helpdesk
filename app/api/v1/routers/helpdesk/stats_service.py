"""Статистика качества работы операторов КС."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import TRACKER_CLOSED_STATUSES, TRACKER_HELPDESK_LIST_SOURCES
from app.api.v1.routers.helpdesk.ticket_service import _support_co_executor_exists_sql

_SOURCES_IN = ", ".join(f"'{s}'" for s in TRACKER_HELPDESK_LIST_SOURCES)
_CLOSED_IN = ", ".join(f"'{s}'::users.tracker_status" for s in TRACKER_CLOSED_STATUSES)

_ENGINEER_LINE_HISTORY_SQL = """
EXISTS (
    SELECT 1
    FROM users.tracker_ticket_line_history lh
    WHERE lh.ticket_id = tt.id
      AND lh.event_type IN ('line_changed', 'escalated_to_engineers')
      AND COALESCE((lh.payload->>'to_line')::int, 0) = 2
)
"""

_ENGINEER_CHAT_MESSAGE_SQL = """
EXISTS (
    SELECT 1
    FROM users.tracker_messages tm
    INNER JOIN users.skystream_users su ON su.id = tm.author_id
    WHERE tm.ticket_id = tt.id
      AND lower(COALESCE(tm.person_type, 'skystream')) IN ('skystream', 'call_centre')
      AND lower(COALESCE(su.role, '')) = 'engineer'
)
OR EXISTS (
    SELECT 1
    FROM users.user_mail um
    INNER JOIN users.skystream_users su ON su.id = um.user_id
    WHERE (
        um.ticket_id = tt.id
        OR EXISTS (
            SELECT 1 FROM users.tracker_ticket_mail_links l
            WHERE l.ticket_id = tt.id AND l.user_mail_id = um.id
        )
    )
      AND lower(COALESCE(um.person_type, '')) IN ('skystream', 'call_centre')
      AND lower(COALESCE(su.role, '')) = 'engineer'
)
"""

_FIRST_RESPONSE_SQL = """
COALESCE(
    tt.first_response_at,
    (SELECT MIN(tm.created_at)
     FROM users.tracker_messages tm
     WHERE tm.ticket_id = tt.id
       AND COALESCE(tm.person_type, 'skystream') IN ('skystream', 'call_centre')),
    (SELECT MIN(COALESCE(um.date_tz, to_timestamp(um.date)))
     FROM users.user_mail um
     WHERE (
         um.ticket_id = tt.id
         OR EXISTS (
             SELECT 1 FROM users.tracker_ticket_mail_links l
             WHERE l.ticket_id = tt.id AND l.user_mail_id = um.id
         )
     )
     AND (
         CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
              THEN um.person_type <> 'user'
              ELSE COALESCE(um.answer, 0) = 1
         END
     ))
)
"""


def _period_params(date_from: date, date_to: date) -> dict[str, Any]:
    return {
        "date_from": datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc),
        "date_to": datetime.combine(date_to, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1),
    }


def _scope_sql(operator_id: int | None, *, alias: str = "tt") -> tuple[str, dict[str, Any]]:
    if operator_id is None:
        return "", {}
    co_exec = _support_co_executor_exists_sql(ticket_expr=f"{alias}.id", user_param=":list_assigned_to")
    sql = f"""AND (
        {alias}.assigned_to = :list_assigned_to
        OR {co_exec}
    )"""
    return sql, {"list_assigned_to": operator_id}


def is_support_admin(*, role: str | None, level: int | None) -> bool:
    return role == "support" and level == 2


async def fetch_support_operators(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, COALESCE(NULLIF(TRIM(full_name), ''), login) AS label
                FROM users.skystream_users
                WHERE role = 'support' AND is_active IS TRUE
                ORDER BY label
                """
            )
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def fetch_stats_summary(
    db: AsyncSession,
    *,
    date_from: date,
    date_to: date,
    operator_id: int | None,
) -> dict[str, Any]:
    scope_sql, scope_params = _scope_sql(operator_id)
    params = {**_period_params(date_from, date_to), **scope_params}

    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) FILTER (
                        WHERE tt.date_of_create >= :date_from
                          AND tt.date_of_create < :date_to
                    )::int AS new_tickets,
                    COUNT(*) FILTER (
                        WHERE tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    )::int AS closed_tickets,
                    AVG(
                        EXTRACT(EPOCH FROM ({_FIRST_RESPONSE_SQL} - tt.date_of_create))
                    ) FILTER (
                        WHERE tt.date_of_create >= :date_from
                          AND tt.date_of_create < :date_to
                          AND {_FIRST_RESPONSE_SQL} IS NOT NULL
                          AND {_FIRST_RESPONSE_SQL} >= tt.date_of_create
                    )::float AS avg_first_response_sec,
                    AVG(EXTRACT(EPOCH FROM (tt.date_of_close - tt.date_of_create))) FILTER (
                        WHERE tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    )::float AS avg_lifetime_sec,
                    (
                        SELECT AVG(ttr.rating)::float
                        FROM users.tracker_tickets_ratings ttr
                        JOIN users.tracker_tickets rt ON rt.id = ttr.ticket_id
                        WHERE COALESCE(rt.source, 'call_center') IN ({_SOURCES_IN})
                          AND rt.status IN ({_CLOSED_IN})
                          AND rt.date_of_close IS NOT NULL
                          AND rt.date_of_close >= :date_from
                          AND rt.date_of_close < :date_to
                          {_scope_sql(operator_id, alias='rt')[0]}
                    ) AS avg_rating
                FROM users.tracker_tickets tt
                WHERE COALESCE(tt.source, 'call_center') IN ({_SOURCES_IN})
                  {scope_sql}
                """
            ),
            params,
        )
    ).mappings().first()

    data = dict(row) if row else {}
    avg_rating = data.get("avg_rating")
    avg_fr = data.get("avg_first_response_sec")
    avg_lt = data.get("avg_lifetime_sec")
    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "new_tickets": int(data.get("new_tickets") or 0),
        "closed_tickets": int(data.get("closed_tickets") or 0),
        "avg_first_response_sec": round(float(avg_fr), 1) if avg_fr is not None else None,
        "avg_lifetime_sec": round(float(avg_lt), 1) if avg_lt is not None else None,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
    }


async def fetch_operator_stats_rows(
    db: AsyncSession,
    *,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    params = _period_params(date_from, date_to)
    co_exec = _support_co_executor_exists_sql(ticket_expr="tt.id", user_param="op.id")

    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    op.id AS operator_id,
                    COALESCE(NULLIF(TRIM(op.full_name), ''), op.login) AS operator_name,
                    COUNT(DISTINCT tt.id) FILTER (
                        WHERE tt.date_of_create >= :date_from
                          AND tt.date_of_create < :date_to
                    )::int AS new_tickets,
                    COUNT(DISTINCT tt.id) FILTER (
                        WHERE tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    )::int AS closed_tickets,
                    AVG(
                        EXTRACT(EPOCH FROM ({_FIRST_RESPONSE_SQL} - tt.date_of_create))
                    ) FILTER (
                        WHERE tt.date_of_create >= :date_from
                          AND tt.date_of_create < :date_to
                          AND {_FIRST_RESPONSE_SQL} IS NOT NULL
                          AND {_FIRST_RESPONSE_SQL} >= tt.date_of_create
                    )::float AS avg_first_response_sec,
                    AVG(EXTRACT(EPOCH FROM (tt.date_of_close - tt.date_of_create))) FILTER (
                        WHERE tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    )::float AS avg_lifetime_sec,
                    AVG(ttr.rating) FILTER (
                        WHERE ttr.rating IS NOT NULL
                          AND tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    )::float AS avg_rating
                FROM users.skystream_users op
                LEFT JOIN users.tracker_tickets tt ON (
                    COALESCE(tt.source, 'call_center') IN ({_SOURCES_IN})
                    AND (
                        tt.assigned_to = op.id
                        OR {co_exec}
                    )
                )
                LEFT JOIN users.tracker_tickets_ratings ttr ON ttr.ticket_id = tt.id
                WHERE op.role = 'support' AND op.is_active IS TRUE
                GROUP BY op.id, op.full_name, op.login
                HAVING COUNT(DISTINCT tt.id) FILTER (
                    WHERE tt.date_of_create >= :date_from AND tt.date_of_create < :date_to
                ) > 0
                    OR COUNT(DISTINCT tt.id) FILTER (
                        WHERE tt.status IN ({_CLOSED_IN})
                          AND tt.date_of_close IS NOT NULL
                          AND tt.date_of_close >= :date_from
                          AND tt.date_of_close < :date_to
                    ) > 0
                ORDER BY closed_tickets DESC NULLS LAST, operator_name
                """
            ),
            params,
        )
    ).mappings().all()

    result: list[dict[str, Any]] = []
    for r in rows:
        avg_fr = r.get("avg_first_response_sec")
        avg_lt = r.get("avg_lifetime_sec")
        avg_rating = r.get("avg_rating")
        result.append(
            {
                "operator_id": int(r["operator_id"]),
                "operator_name": r["operator_name"],
                "new_tickets": int(r.get("new_tickets") or 0),
                "closed_tickets": int(r.get("closed_tickets") or 0),
                "avg_first_response_sec": round(float(avg_fr), 1) if avg_fr is not None else None,
                "avg_lifetime_sec": round(float(avg_lt), 1) if avg_lt is not None else None,
                "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
            }
        )
    return result


async def fetch_recent_ratings(
    db: AsyncSession,
    *,
    date_from: date,
    date_to: date,
    operator_id: int | None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    scope_sql, scope_params = _scope_sql(operator_id)
    params = {**_period_params(date_from, date_to), **scope_params, "limit": limit}

    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    tt.id AS ticket_id,
                    COALESCE(tt.source, 'call_center') AS source,
                    ttr.rating,
                    ttr.comment AS rating_comment,
                    COALESCE(tt.date_of_close, tt.updated_at, tt.date_of_create) AS rated_at,
                    EXTRACT(EPOCH FROM (tt.date_of_close - tt.date_of_create))::float AS lifetime_sec,
                    tc.name AS category_label,
                    (
                        {_ENGINEER_LINE_HISTORY_SQL}
                        OR ({_ENGINEER_CHAT_MESSAGE_SQL})
                    ) AS engineer_involved
                FROM users.tracker_tickets_ratings ttr
                JOIN users.tracker_tickets tt ON tt.id = ttr.ticket_id
                LEFT JOIN users.ticket_categories tc ON tc.id = tt.category_id
                WHERE COALESCE(tt.source, 'call_center') IN ({_SOURCES_IN})
                  AND tt.status IN ({_CLOSED_IN})
                  AND COALESCE(tt.date_of_close, tt.updated_at, tt.date_of_create) >= :date_from
                  AND COALESCE(tt.date_of_close, tt.updated_at, tt.date_of_create) < :date_to
                  {scope_sql}
                ORDER BY rated_at DESC NULLS LAST
                LIMIT :limit
                """
            ),
            params,
        )
    ).mappings().all()

    from app.constants import SOURCE_DISPLAY

    out: list[dict[str, Any]] = []
    for r in rows:
        src = r.get("source") or "call_center"
        rated_at = r.get("rated_at")
        lifetime_sec = r.get("lifetime_sec")
        out.append(
            {
                "ticket_id": int(r["ticket_id"]),
                "source": src,
                "source_label": SOURCE_DISPLAY.get(src, src),
                "rating": int(r["rating"]) if r.get("rating") is not None else None,
                "rating_comment": r.get("rating_comment"),
                "rated_at": rated_at.isoformat() if rated_at is not None else None,
                "lifetime_sec": round(float(lifetime_sec), 1) if lifetime_sec is not None else None,
                "category_label": (r.get("category_label") or "").strip() or None,
                "engineer_involved": bool(r.get("engineer_involved")),
            }
        )
    return out
