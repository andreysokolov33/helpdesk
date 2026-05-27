"""Порционная загрузка сообщений тикета (user_mail / tracker_messages)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CHAT_PAGE_SIZE = 40
CHAT_AROUND_HALF = 20

_MAIL_ANSWER_EXPR = """
    CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
         THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
         ELSE um.answer END
"""

_MAIL_SELECT = f"""
    SELECT um.id AS msg_id, um.id_user_from, um.date_tz, um.updated_at,
        um.person_type, um.user_id,
        ({_MAIL_ANSWER_EXPR}) AS answer,
        um.text AS text_raw,
        CASE WHEN um.file_new IS NULL OR um.file_new IN ('0', '') THEN NULL
             ELSE um.file_new END AS legacy_file,
        um.relay_msg_id,
        su.full_name AS staff_full_name,
        su.role AS staff_role
    FROM users.user_mail um
    LEFT JOIN users.skystream_users su
        ON um.user_id = su.id AND COALESCE(um.person_type, '') = 'skystream'
"""


def _ticket_svc():
    from app.api.v1.routers.helpdesk import ticket_service as svc

    return svc


async def _mail_scope(
    db: AsyncSession,
    ticket_id: int,
    subscriber_id: int | None,
) -> tuple[str, dict[str, Any]]:
    svc = _ticket_svc()
    cnt = (
        await db.execute(
            text("SELECT COUNT(*)::int FROM users.user_mail WHERE ticket_id = :tid"),
            {"tid": ticket_id},
        )
    ).scalar()
    if int(cnt or 0) > 0:
        return "ticket", {"ticket_id": ticket_id}
    if subscriber_id is not None:
        start_id, end_id = await svc._mail_link_bounds(db, ticket_id)
        if start_id is not None and end_id is not None:
            return "link", {
                "start_id": start_id,
                "end_id": end_id,
                "subscriber_id": subscriber_id,
            }
    return "empty", {}


def _mail_where(scope_kind: str) -> str:
    if scope_kind == "ticket":
        return "um.ticket_id = :ticket_id"
    return """
        um.id BETWEEN :start_id AND :end_id
        AND :subscriber_id IN (um.id_user_from, um.id_user_to)
    """


async def _mail_exists_beyond(
    db: AsyncSession,
    scope_kind: str,
    scope_params: dict[str, Any],
    msg_id: int,
    *,
    older: bool,
) -> bool:
    op = "<" if older else ">"
    where = _mail_where(scope_kind)
    row = (
        await db.execute(
            text(
                f"""
                SELECT 1 FROM users.user_mail um
                WHERE {where} AND um.id {op} :mid
                LIMIT 1
                """
            ),
            {**scope_params, "mid": msg_id},
        )
    ).scalar()
    return bool(row)


async def _mail_fetch_rows(
    db: AsyncSession,
    scope_kind: str,
    scope_params: dict[str, Any],
    *,
    limit: int,
    before_id: int | None = None,
    after_id: int | None = None,
    around_id: int | None = None,
    since_id: int = 0,
) -> list[Any]:
    if scope_kind == "empty":
        return []

    where = _mail_where(scope_kind)
    params: dict[str, Any] = {**scope_params}

    if since_id > 0:
        return (
            await db.execute(
                text(
                    f"""
                    {_MAIL_SELECT}
                    WHERE {where} AND um.id > :since_id
                    ORDER BY COALESCE(um.date_tz, to_timestamp(um.date)), um.id
                    """
                ),
                {**params, "since_id": since_id},
            )
        ).mappings().all()

    if around_id is not None:
        half = CHAT_AROUND_HALF
        older = (
            await db.execute(
                text(
                    f"""
                    SELECT * FROM (
                        {_MAIL_SELECT}
                        WHERE {where} AND um.id < :around_id
                        ORDER BY um.id DESC
                        LIMIT :half
                    ) sub ORDER BY msg_id ASC
                    """
                ),
                {**params, "around_id": around_id, "half": half},
            )
        ).mappings().all()
        center = (
            await db.execute(
                text(f"{_MAIL_SELECT} WHERE {where} AND um.id = :around_id"),
                {**params, "around_id": around_id},
            )
        ).mappings().all()
        newer = (
            await db.execute(
                text(
                    f"""
                    {_MAIL_SELECT}
                    WHERE {where} AND um.id > :around_id
                    ORDER BY um.id ASC
                    LIMIT :half
                    """
                ),
                {**params, "around_id": around_id, "half": half},
            )
        ).mappings().all()
        return list(older) + list(center) + list(newer)

    if before_id is not None:
        return (
            await db.execute(
                text(
                    f"""
                    SELECT * FROM (
                        {_MAIL_SELECT}
                        WHERE {where} AND um.id < :before_id
                        ORDER BY um.id DESC
                        LIMIT :limit
                    ) sub ORDER BY msg_id ASC
                    """
                ),
                {**params, "before_id": before_id, "limit": limit},
            )
        ).mappings().all()

    if after_id is not None:
        return (
            await db.execute(
                text(
                    f"""
                    {_MAIL_SELECT}
                    WHERE {where} AND um.id > :after_id
                    ORDER BY um.id ASC
                    LIMIT :limit
                    """
                ),
                {**params, "after_id": after_id, "limit": limit},
            )
        ).mappings().all()

    return (
        await db.execute(
            text(
                f"""
                SELECT * FROM (
                    {_MAIL_SELECT}
                    WHERE {where}
                    ORDER BY um.id DESC
                    LIMIT :limit
                ) sub ORDER BY msg_id ASC
                """
            ),
            {**params, "limit": limit},
        )
    ).mappings().all()


async def mail_rows_to_messages(
    db: AsyncSession,
    rows: list[Any],
    *,
    viewer_id: int,
    subscriber_display_name: str,
) -> list[dict[str, Any]]:
    from datetime import datetime

    svc = _ticket_svc()
    msg_ids = [int(r["msg_id"]) for r in rows]
    att_map = await svc._attachments_map(db, msg_ids, tracker=False)

    read_ids: set[int] = set()
    if msg_ids:
        read_ids = {
            int(x)
            for x in (
                await db.execute(
                    text(
                        """
                        SELECT DISTINCT msg_id FROM users.user_mail_reads
                        WHERE msg_id = ANY(:ids) AND person_type = ANY(:staff_types)
                        """
                    ),
                    {"ids": msg_ids, "staff_types": list(svc.STAFF_READ_PERSON_TYPES)},
                )
            ).scalars().all()
        }

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["msg_id"])
        is_bot = int(r.get("id_user_from") or 0) == 0
        is_out = int(r["answer"] or 0) == 1
        dt = r.get("date_tz")
        legacy = r.get("legacy_file")
        side, author_name = svc._classify_mail_message(
            viewer_id=viewer_id,
            is_bot=is_bot,
            is_out=is_out,
            person_type=r.get("person_type"),
            author_id=int(r["user_id"]) if r.get("user_id") is not None else None,
            staff_full_name=r.get("staff_full_name"),
            staff_role=r.get("staff_role"),
            subscriber_name=subscriber_display_name,
        )
        is_incoming_client = side == "client"
        edit_meta = svc._message_edit_meta(updated_at=r.get("updated_at"))
        messages.append(
            {
                "id": mid,
                "side": side,
                "text": (r.get("text_raw") or "").strip(),
                "author_name": author_name,
                "created_at_iso": svc._iso(dt) if isinstance(dt, datetime) else None,
                "has_read": True
                if is_bot or side == "me"
                else mid in read_ids or not is_incoming_client,
                "reply_to_id": svc._parse_reply_to_id(r.get("relay_msg_id")),
                **edit_meta,
                "legacy_file_url": svc._media_url(legacy) if legacy else None,
                "attachments": att_map.get(mid, []),
            }
        )
    return messages


async def load_mail_messages_paged(
    db: AsyncSession,
    ticket_id: int,
    subscriber_id: int | None,
    viewer_id: int,
    *,
    subscriber_display_name: str = "Абонент",
    limit: int = CHAT_PAGE_SIZE,
    before_id: int | None = None,
    after_id: int | None = None,
    around_id: int | None = None,
    since_id: int = 0,
    include_initial_body: str | None = None,
) -> tuple[list[dict[str, Any]], bool, bool]:
    scope_kind, scope_params = await _mail_scope(db, ticket_id, subscriber_id)
    rows = await _mail_fetch_rows(
        db,
        scope_kind,
        scope_params,
        limit=limit,
        before_id=before_id,
        after_id=after_id,
        around_id=around_id,
        since_id=since_id,
    )
    messages = await mail_rows_to_messages(
        db,
        rows,
        viewer_id=viewer_id,
        subscriber_display_name=subscriber_display_name,
    )

    if since_id > 0:
        return messages, False, False

    ids = [int(m["id"]) for m in messages if int(m["id"]) > 0]
    has_older = False
    has_newer = False
    if ids and scope_kind != "empty":
        min_id, max_id = min(ids), max(ids)
        has_older = await _mail_exists_beyond(
            db, scope_kind, scope_params, min_id, older=True
        )
        has_newer = await _mail_exists_beyond(
            db, scope_kind, scope_params, max_id, older=False
        )

    if (
        not messages
        and include_initial_body
        and include_initial_body.strip()
        and since_id <= 0
        and before_id is None
        and after_id is None
        and around_id is None
    ):
        messages.append(
            {
                "id": 0,
                "side": "client",
                "text": include_initial_body.strip(),
                "author_name": subscriber_display_name,
                "created_at_iso": None,
                "has_read": True,
                "reply_to_id": None,
                "is_edited": False,
                "updated_at_iso": None,
                "legacy_file_url": None,
                "attachments": [],
                "is_initial": True,
            }
        )

    return messages, has_older, has_newer


_TRACKER_SELECT = """
    SELECT tm.id, tm.body, tm.created_at, tm.updated_at, tm.author_id, tm.person_type,
        tm.reply_to_id, tm.is_edited,
        su.full_name AS staff_full_name,
        su.role AS staff_role
    FROM users.tracker_messages tm
    LEFT JOIN users.skystream_users su ON su.id = tm.author_id
"""


async def _tracker_exists_beyond(
    db: AsyncSession,
    ticket_id: int,
    msg_id: int,
    *,
    older: bool,
) -> bool:
    op = "<" if older else ">"
    row = (
        await db.execute(
            text(
                f"""
                SELECT 1 FROM users.tracker_messages
                WHERE ticket_id = :tid AND id {op} :mid
                LIMIT 1
                """
            ),
            {"tid": ticket_id, "mid": msg_id},
        )
    ).scalar()
    return bool(row)


async def _tracker_fetch_rows(
    db: AsyncSession,
    ticket_id: int,
    *,
    limit: int,
    before_id: int | None = None,
    after_id: int | None = None,
    around_id: int | None = None,
    since_id: int = 0,
) -> list[Any]:
    if since_id > 0:
        return (
            await db.execute(
                text(
                    f"""
                    {_TRACKER_SELECT}
                    WHERE tm.ticket_id = :ticket_id AND tm.id > :since_id
                    ORDER BY tm.created_at, tm.id
                    """
                ),
                {"ticket_id": ticket_id, "since_id": since_id},
            )
        ).mappings().all()

    if around_id is not None:
        half = CHAT_AROUND_HALF
        older = (
            await db.execute(
                text(
                    f"""
                    SELECT * FROM (
                        {_TRACKER_SELECT}
                        WHERE tm.ticket_id = :ticket_id AND tm.id < :around_id
                        ORDER BY tm.id DESC
                        LIMIT :half
                    ) sub ORDER BY id ASC
                    """
                ),
                {"ticket_id": ticket_id, "around_id": around_id, "half": half},
            )
        ).mappings().all()
        center = (
            await db.execute(
                text(
                    f"{_TRACKER_SELECT} WHERE tm.ticket_id = :ticket_id AND tm.id = :around_id"
                ),
                {"ticket_id": ticket_id, "around_id": around_id},
            )
        ).mappings().all()
        newer = (
            await db.execute(
                text(
                    f"""
                    {_TRACKER_SELECT}
                    WHERE tm.ticket_id = :ticket_id AND tm.id > :around_id
                    ORDER BY tm.id ASC
                    LIMIT :half
                    """
                ),
                {"ticket_id": ticket_id, "around_id": around_id, "half": half},
            )
        ).mappings().all()
        return list(older) + list(center) + list(newer)

    if before_id is not None:
        return (
            await db.execute(
                text(
                    f"""
                    SELECT * FROM (
                        {_TRACKER_SELECT}
                        WHERE tm.ticket_id = :ticket_id AND tm.id < :before_id
                        ORDER BY tm.id DESC
                        LIMIT :limit
                    ) sub ORDER BY id ASC
                    """
                ),
                {"ticket_id": ticket_id, "before_id": before_id, "limit": limit},
            )
        ).mappings().all()

    if after_id is not None:
        return (
            await db.execute(
                text(
                    f"""
                    {_TRACKER_SELECT}
                    WHERE tm.ticket_id = :ticket_id AND tm.id > :after_id
                    ORDER BY tm.id ASC
                    LIMIT :limit
                    """
                ),
                {"ticket_id": ticket_id, "after_id": after_id, "limit": limit},
            )
        ).mappings().all()

    return (
        await db.execute(
            text(
                f"""
                SELECT * FROM (
                    {_TRACKER_SELECT}
                    WHERE tm.ticket_id = :ticket_id
                    ORDER BY tm.id DESC
                    LIMIT :limit
                ) sub ORDER BY id ASC
                """
            ),
            {"ticket_id": ticket_id, "limit": limit},
        )
    ).mappings().all()


async def tracker_rows_to_messages(
    db: AsyncSession,
    rows: list[Any],
    *,
    viewer_id: int,
    subscriber_display_name: str,
) -> list[dict[str, Any]]:
    svc = _ticket_svc()
    msg_ids = [int(r["id"]) for r in rows]
    att_map = await svc._attachments_map(db, msg_ids, tracker=True)

    staff_read_ids: set[int] = set()
    if msg_ids:
        staff_read_ids = {
            int(x)
            for x in (
                await db.execute(
                    text(
                        """
                        SELECT DISTINCT msg_id FROM users.tracker_messages_reads
                        WHERE msg_id = ANY(:ids) AND person_type = ANY(:staff_types)
                        """
                    ),
                    {"ids": msg_ids, "staff_types": list(svc.STAFF_READ_PERSON_TYPES)},
                )
            ).scalars().all()
        }

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["id"])
        author_id = int(r["author_id"])
        side, author_name = svc._classify_tracker_message(
            viewer_id=viewer_id,
            author_id=author_id,
            person_type=r.get("person_type"),
            staff_full_name=r.get("staff_full_name"),
            staff_role=r.get("staff_role"),
            subscriber_name=subscriber_display_name,
        )
        is_own = side == "me"
        edit_meta = svc._message_edit_meta(
            updated_at=r.get("updated_at"),
            is_edited_flag=bool(r.get("is_edited")),
        )
        messages.append(
            {
                "id": mid,
                "side": side,
                "text": (r.get("body") or "").strip(),
                "author_name": author_name,
                "created_at_iso": svc._iso(r.get("created_at")),
                "has_read": is_own or mid in staff_read_ids or side != "client",
                "reply_to_id": svc._parse_reply_to_id(r.get("reply_to_id")),
                **edit_meta,
                "legacy_file_url": None,
                "attachments": att_map.get(mid, []),
            }
        )
    return messages


async def load_tracker_messages_paged(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    viewer_role: str,
    *,
    subscriber_display_name: str = "Абонент",
    limit: int = CHAT_PAGE_SIZE,
    before_id: int | None = None,
    after_id: int | None = None,
    around_id: int | None = None,
    since_id: int = 0,
) -> tuple[list[dict[str, Any]], bool, bool]:
    del viewer_role  # reserved
    rows = await _tracker_fetch_rows(
        db,
        ticket_id,
        limit=limit,
        before_id=before_id,
        after_id=after_id,
        around_id=around_id,
        since_id=since_id,
    )
    messages = await tracker_rows_to_messages(
        db,
        rows,
        viewer_id=viewer_id,
        subscriber_display_name=subscriber_display_name,
    )

    if since_id > 0:
        return messages, False, False

    ids = [int(m["id"]) for m in messages]
    has_older = False
    has_newer = False
    if ids:
        has_older = await _tracker_exists_beyond(db, ticket_id, min(ids), older=True)
        has_newer = await _tracker_exists_beyond(db, ticket_id, max(ids), older=False)
    return messages, has_older, has_newer
