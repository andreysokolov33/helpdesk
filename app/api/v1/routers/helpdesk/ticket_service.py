"""Карточка тикета: шапка, сообщения user_mail / tracker_messages, отправка, вложения."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import PRIORITY_DICT, SOURCE_DISPLAY, STATUS_DISPLAY, TRACKER_OPEN_STATUSES
from app.models.users import (
    TrackerMessageAttachment,
    TrackerMessages,
    UserMailAttachment,
)

TRACKER_CHAT_SOURCES = frozenset({"ks", "partner", "tech", "incidents", "abs"})
_MOSCOW = ZoneInfo("Europe/Moscow")
_MEDIA_ROOT = os.path.abspath(settings.MEDIA_DIR)
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_ALLOWED_EXT = _IMAGE_EXT | {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"}


def chat_mode_for_source(source: str | None) -> str:
    return "tracker" if (source or "call_center") in TRACKER_CHAT_SOURCES else "mail"


def _moscow_ts() -> int:
    return int(datetime.now(_MOSCOW).timestamp())


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _media_url(file_path: str | None) -> str | None:
    if not file_path or file_path in ("0", ""):
        return None
    p = file_path.strip()
    if p.startswith("/media/"):
        return p
    if p.startswith("media/"):
        return "/" + p
    return f"/media/{p.lstrip('/')}"


async def load_ticket_detail(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                """
                SELECT tt.id, tt.title, tt.body, tt.status::text AS status_raw,
                    tt.support_line, tt.date_of_create, tt.date_of_close, tt.updated_at,
                    COALESCE(tt.source, 'call_center') AS source,
                    COALESCE(tt.person_type, 'user') AS person_type,
                    COALESCE(tt.object_type, 'user') AS object_type,
                    tt.user_id, tt.caller_name, tt.station_id, tt.hotspot_id, tt.vno,
                    tt.category_id, tt.assigned_to, tt.author,
                    COALESCE(tt.priority::text, tc.priority::text) AS priority,
                    tc.name AS category_name,
                    tcp.name AS category_parent_name,
                    u.login AS subscriber_login,
                    u.is_juridical,
                    CASE
                        WHEN tt.person_type = 'cs' AND NULLIF(TRIM(tt.caller_name), '') IS NOT NULL
                            THEN TRIM(tt.caller_name)
                        WHEN u.is_juridical = 2 THEN jcl.short_name_organization
                        WHEN u.is_juridical = 0 THEN NULLIF(TRIM(
                            CONCAT_WS(' ', ud.surname, ud.name, ud.patronymic)), '')
                        ELSE u.full_name
                    END AS subscriber_name,
                    su.full_name AS assignee_name,
                    su.role AS assignee_role,
                    sf.station_name,
                    ig.name AS station_fallback_name
                FROM users.tracker_tickets tt
                LEFT JOIN users.ticket_categories tc ON tc.id = tt.category_id
                LEFT JOIN users.ticket_categories tcp ON tcp.id = tc.parent_id
                LEFT JOIN users."user" u ON u.id = tt.user_id
                    AND COALESCE(tt.object_type, 'user') = 'user'
                LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.juridical_id
                LEFT JOIN LATERAL (
                    SELECT ud.surname, ud.name, ud.patronymic
                    FROM users.user_details ud
                    WHERE ud.user_id = u.id AND ud.is_actual IS TRUE
                    ORDER BY ud.id DESC
                    LIMIT 1
                ) ud ON TRUE
                LEFT JOIN users.skystream_users su ON su.id = tt.assigned_to
                LEFT JOIN wifitochka.ip_group ig ON ig.id = COALESCE(tt.station_id, u.id_grp)
                LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
                WHERE tt.id = :ticket_id
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    d = dict(row)
    status_raw = d.get("status_raw") or "pending"
    source = d.get("source") or "call_center"
    line = int(d.get("support_line") or 1)
    line_labels = {1: "КС", 2: "Инженеры", 3: "Партнёр"}
    pr = d.get("priority")
    cat = d.get("category_name")
    cat_parent = d.get("category_parent_name")
    category_label = f"{cat_parent} / {cat}" if cat_parent and cat else (cat or cat_parent)

    assigned_at_row = (
        await db.execute(
            text(
                """
                SELECT start_time
                FROM users.tracker_ticket_line_history
                WHERE ticket_id = :ticket_id AND support_line IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().first()

    station = (d.get("station_name") or d.get("station_fallback_name") or "").strip() or None
    sub_name = (d.get("subscriber_name") or "").strip()
    sub_login = (d.get("subscriber_login") or "").strip()
    if not sub_name and d.get("user_id"):
        sub_name = sub_login or f"Абонент #{d['user_id']}"
    if not sub_name and d.get("caller_name"):
        sub_name = str(d["caller_name"]).strip()

    return {
        "id": int(d["id"]),
        "title": d.get("title") or f"Тикет #{ticket_id}",
        "body": d.get("body"),
        "status": status_raw,
        "status_label": STATUS_DISPLAY.get(status_raw, status_raw),
        "is_open": status_raw in TRACKER_OPEN_STATUSES,
        "priority": pr,
        "priority_label": PRIORITY_DICT.get(pr, pr) if pr else None,
        "support_line": line,
        "support_line_label": line_labels.get(line, str(line)),
        "source": source,
        "source_label": SOURCE_DISPLAY.get(source, source),
        "category_label": category_label,
        "user_id": int(d["user_id"]) if d.get("user_id") is not None else None,
        "caller_name": d.get("caller_name"),
        "subscriber_name": sub_name or None,
        "subscriber_login": sub_login or None,
        "subscriber_is_juridical": int(d.get("is_juridical") or 0),
        "subscriber_profile_user_id": int(d["user_id"]) if d.get("user_id") is not None else None,
        "assignee_name": d.get("assignee_name"),
        "assignee_role": d.get("assignee_role"),
        "assignee_is_viewer": bool(d.get("assigned_to") and int(d["assigned_to"]) == viewer_id),
        "station_name": station,
        "station_id": int(d["station_id"]) if d.get("station_id") else None,
        "date_of_create": d["date_of_create"],
        "date_of_create_iso": _iso(d.get("date_of_create")),
        "updated_at": d.get("updated_at"),
        "updated_at_iso": _iso(d.get("updated_at")),
        "assigned_at_iso": _iso(assigned_at_row["start_time"]) if assigned_at_row else None,
        "chat_mode": chat_mode_for_source(source),
        "can_reply": d.get("user_id") is not None,
    }


async def _mail_link_bounds(db: AsyncSession, ticket_id: int) -> tuple[int | None, int | None]:
    row = (
        await db.execute(
            text(
                """
                SELECT MIN(user_mail_id) AS min_id, MAX(user_mail_id) AS max_id
                FROM users.tracker_ticket_mail_links
                WHERE ticket_id = :ticket_id
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().first()
    if not row or row["min_id"] is None:
        return None, None
    return int(row["min_id"]), int(row["max_id"])


async def _attachments_map(db: AsyncSession, msg_ids: list[int], *, tracker: bool) -> dict[int, list[dict]]:
    if not msg_ids:
        return {}
    if tracker:
        stmt = select(TrackerMessageAttachment).where(TrackerMessageAttachment.msg_id.in_(msg_ids))
        rows = (await db.execute(stmt)).scalars().all()
    else:
        stmt = select(UserMailAttachment).where(UserMailAttachment.msg_id.in_(msg_ids))
        rows = (await db.execute(stmt)).scalars().all()
    out: dict[int, list[dict]] = {mid: [] for mid in msg_ids}
    for r in rows:
        fp = _media_url(r.file_path)
        out[int(r.msg_id)].append(
            {
                "id": int(r.id),
                "file_path": fp or r.file_path,
                "original_filename": r.original_filename or "",
                "file_ext": r.file_ext,
                "file_size_bytes": r.file_size_bytes,
                "is_image": (r.file_ext or "").lower() in {e.lstrip(".") for e in _IMAGE_EXT}
                or (r.file_path or "").lower().endswith(tuple(_IMAGE_EXT)),
            }
        )
    return out


async def load_mail_messages(
    db: AsyncSession,
    ticket_id: int,
    subscriber_id: int | None,
    viewer_id: int,
    *,
    include_initial_body: str | None = None,
) -> list[dict[str, Any]]:
    answer_expr = """
        CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
             THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
             ELSE um.answer END
    """
    rows = (
        await db.execute(
            text(
                f"""
                SELECT um.id AS msg_id, um.date_tz, ({answer_expr}) AS answer,
                    um.text AS text_raw,
                    CASE WHEN um.file_new IS NULL OR um.file_new IN ('0', '') THEN NULL
                         ELSE um.file_new END AS legacy_file,
                    um.relay_msg_id
                FROM users.user_mail um
                WHERE um.ticket_id = :ticket_id
                ORDER BY COALESCE(um.date_tz, to_timestamp(um.date)), um.id
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().all()

    if not rows and subscriber_id is not None:
        start_id, end_id = await _mail_link_bounds(db, ticket_id)
        if start_id is not None and end_id is not None:
            rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT um.id AS msg_id, um.date_tz, ({answer_expr}) AS answer,
                            um.text AS text_raw,
                            CASE WHEN um.file_new IS NULL OR um.file_new IN ('0', '') THEN NULL
                                 ELSE um.file_new END AS legacy_file,
                            um.relay_msg_id
                        FROM users.user_mail um
                        WHERE um.id BETWEEN :start_id AND :end_id
                          AND :subscriber_id IN (um.id_user_from, um.id_user_to)
                        ORDER BY COALESCE(um.date_tz, to_timestamp(um.date)), um.id
                        """
                    ),
                    {
                        "start_id": start_id,
                        "end_id": end_id,
                        "subscriber_id": subscriber_id,
                    },
                )
            ).mappings().all()

    msg_ids = [int(r["msg_id"]) for r in rows]
    att_map = await _attachments_map(db, msg_ids, tracker=False)

    read_ids: set[int] = set()
    if msg_ids:
        read_rows = (
            await db.execute(
                text(
                    """
                    SELECT msg_id FROM users.user_mail_reads
                    WHERE msg_id = ANY(:ids) AND user_id = :viewer_id
                    """
                ),
                {"ids": msg_ids, "viewer_id": viewer_id},
            )
        ).scalars().all()
        read_ids = {int(x) for x in read_rows}

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["msg_id"])
        is_out = int(r["answer"] or 0) == 1
        dt = r.get("date_tz")
        legacy = r.get("legacy_file")
        messages.append(
            {
                "id": mid,
                "side": "agent" if is_out else "client",
                "text": (r.get("text_raw") or "").strip(),
                "created_at_iso": _iso(dt) if isinstance(dt, datetime) else None,
                "has_read": mid in read_ids or is_out,
                "legacy_file_url": _media_url(legacy) if legacy else None,
                "attachments": att_map.get(mid, []),
            }
        )

    if not messages and include_initial_body and include_initial_body.strip():
        messages.append(
            {
                "id": 0,
                "side": "client",
                "text": include_initial_body.strip(),
                "created_at_iso": None,
                "has_read": True,
                "legacy_file_url": None,
                "attachments": [],
                "is_initial": True,
            }
        )

    return messages


async def load_tracker_messages(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    viewer_role: str,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT tm.id, tm.body, tm.created_at, tm.author_id, tm.person_type,
                    su.full_name AS author_name
                FROM users.tracker_messages tm
                LEFT JOIN users.skystream_users su ON su.id = tm.author_id
                WHERE tm.ticket_id = :ticket_id
                ORDER BY tm.created_at, tm.id
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().all()

    msg_ids = [int(r["id"]) for r in rows]
    att_map = await _attachments_map(db, msg_ids, tracker=True)

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["id"])
        author_id = int(r["author_id"])
        is_own = author_id == viewer_id
        pt = (r.get("person_type") or "skystream").lower()
        if is_own:
            side = "agent"
        elif pt in ("partner", "tech"):
            side = "partner"
        else:
            side = "client" if pt == "user" else "agent"
        messages.append(
            {
                "id": mid,
                "side": side,
                "text": (r.get("body") or "").strip(),
                "author_name": r.get("author_name") or ("Вы" if is_own else "—"),
                "created_at_iso": _iso(r.get("created_at")),
                "has_read": is_own,
                "legacy_file_url": None,
                "attachments": att_map.get(mid, []),
            }
        )
    return messages


async def mark_mail_messages_read(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    message_ids: list[int],
) -> None:
    if not message_ids:
        return
    for mid in message_ids:
        if mid <= 0:
            continue
        exists = (
            await db.execute(
                text("SELECT 1 FROM users.user_mail WHERE id = :mid AND ticket_id = :tid LIMIT 1"),
                {"mid": mid, "tid": ticket_id},
            )
        ).scalar()
        if not exists:
            continue
        await db.execute(
            text(
                """
                INSERT INTO users.user_mail_reads (msg_id, user_id, person_type, read_time)
                VALUES (:msg_id, :user_id, 'skystream', NOW())
                ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
                """
            ),
            {"msg_id": mid, "user_id": viewer_id},
        )
    await db.commit()


async def send_mail_reply(
    db: AsyncSession,
    ticket_id: int,
    chat_id: int,
    operator_id: int,
    text_body: str,
    *,
    client_ip: str = "0.0.0.0",
    file: UploadFile | None = None,
) -> dict[str, Any]:
    text_body = text_body.strip()
    if not text_body and (not file or not file.filename):
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    ticket = (
        await db.execute(
            text("SELECT id, user_id FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if int(ticket["user_id"] or 0) != chat_id:
        raise HTTPException(status_code=400, detail="Абонент не привязан к тикету")

    file_path = ""
    real_file = None
    moscow_ts = _moscow_ts()
    if file and file.filename:
        file_path, real_file = await _save_upload(file, chat_id)

    ins = (
        await db.execute(
            text(
                """
                INSERT INTO users.user_mail (
                    text, id_user_from, id_user_to, read, answer, date, file_new,
                    user_id, person_type, user_chat, ticket_id, ip_address, date_tz
                )
                VALUES (
                    :text, :from_id, :to_id, '0', 1, :ts, :file_new,
                    :op_id, 'skystream', :chat_id, :ticket_id,
                    CAST(:ip AS inet), NOW()
                )
                RETURNING id, date_tz
                """
            ),
            {
                "text": text_body,
                "from_id": operator_id,
                "to_id": chat_id,
                "ts": moscow_ts,
                "file_new": file_path or "",
                "op_id": operator_id,
                "chat_id": chat_id,
                "ticket_id": ticket_id,
                "ip": client_ip or "127.0.0.1",
            },
        )
    ).mappings().first()
    msg_id = int(ins["id"])
    created = ins.get("date_tz")

    now = datetime.now(timezone.utc)
    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET updated_at = :now
            WHERE id = :ticket_id
            """
        ),
        {"now": now, "ticket_id": ticket_id},
    )
    await db.commit()

    return {
        "id": msg_id,
        "side": "agent",
        "text": text_body,
        "created_at_iso": _iso(created if isinstance(created, datetime) else now),
        "has_read": True,
        "legacy_file_url": _media_url(file_path) if file_path else None,
        "attachments": [],
    }


async def send_tracker_reply(
    db: AsyncSession,
    ticket_id: int,
    operator_id: int,
    text_body: str,
) -> dict[str, Any]:
    text_body = text_body.strip()
    if not text_body:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    now = datetime.now(timezone.utc)
    msg = TrackerMessages(
        ticket_id=ticket_id,
        author_id=operator_id,
        body=text_body,
        created_at=now,
        person_type="skystream",
    )
    db.add(msg)
    await db.flush()
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = :now WHERE id = :tid"),
        {"now": now, "tid": ticket_id},
    )
    await db.commit()

    return {
        "id": int(msg.id),
        "side": "agent",
        "text": text_body,
        "author_name": "Вы",
        "created_at_iso": _iso(now),
        "has_read": True,
        "attachments": [],
    }


async def _save_upload(file: UploadFile, chat_id: int) -> tuple[str, str | None]:
    orig = (file.filename or "file").strip()
    ext = os.path.splitext(orig)[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail="Разрешены изображения, PDF, Word, Excel, CSV",
        )
    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл больше 15 МБ")

    stored = f"{uuid.uuid4().hex}{ext}"
    subdir = f"chat/{chat_id}"
    full_dir = os.path.join(_MEDIA_ROOT, subdir)
    os.makedirs(full_dir, exist_ok=True)
    full_path = os.path.join(full_dir, stored)
    with open(full_path, "wb") as f:
        f.write(contents)
    url = f"/media/{subdir}/{stored}"
    return url, full_path
