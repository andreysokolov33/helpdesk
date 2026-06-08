"""Чат с абонентом (поддержка ↔ абонент).

Виртуальный чат: chat_id == id абонента (users.user.id). Сообщения хранятся в
users.user_mail и группируются по user_chat. Эндпоинты адаптированы из внешнего
проекта под инфраструктуру helpdesk (require_tracker_user, get_db, ORM-модели).
"""

from __future__ import annotations

import html
import json
import logging
import math
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.config import settings
from app.core.ticket_message_validation import html_to_plain_text
from app.database import get_db, redis_client
from app.models.users import UserMail, UserMailAttachment

logger = logging.getLogger("abs")

router = APIRouter(prefix="/v1/helpdesk/chats", tags=["Helpdesk — чат с абонентом"])

# ─────────────────────────────────────────────────────────────────────────────
# Константы
# ─────────────────────────────────────────────────────────────────────────────

_RELAY_SNIPPET_RAW_MAX = 800
MAX_ATTACHMENT_SIZE_BYTES = 15 * 1024 * 1024  # 15 МБ на файл
_UNREAD_CACHE_TTL = 10  # сек
_SUBSCRIBER_ID_THRESHOLD = 1020  # id > 1020 — сообщение от абонента (см. ТЗ §7)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

# Сигнатуры начала файла (magic bytes) — защита от подмены расширения.
_MAGIC_SIGNATURES = [
    (b"%PDF", [".pdf"]),
    (b"\xff\xd8\xff", [".jpg", ".jpeg"]),
    (b"\x89PNG\r\n\x1a\n", [".png"]),
    (b"GIF87a", [".gif"]),
    (b"GIF89a", [".gif"]),
    (b"BM", [".bmp"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные утилиты
# ─────────────────────────────────────────────────────────────────────────────


def _client_ip(request: Request) -> Optional[str]:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip() or None
    return request.client.host if request.client else None


def _operator(user: Dict[str, Any]) -> Dict[str, Any]:
    return {"user_id": int(user["user_id"]), "role": user.get("role")}


def _check_image_magic(contents: bytes, ext: str) -> bool:
    """Содержимое соответствует расширению изображения по magic bytes."""
    if len(contents) < 12:
        return False
    ext = ext.lower()
    if ext == ".webp":
        return contents.startswith(b"RIFF") and contents[8:12] == b"WEBP"
    for magic, exts in _MAGIC_SIGNATURES:
        if ext in exts and contents.startswith(magic):
            return True
    return False


def _is_image_ext(ext: Optional[str]) -> bool:
    return bool(ext) and ext.lower() in ALLOWED_IMAGE_EXTENSIONS


_SCRIPT_RE = re.compile(r"<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
_EVENT_ATTR_RE = re.compile(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_JS_URI_RE = re.compile(r"(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\2", re.I)


def _sanitize_html(raw: str) -> str:
    """Лёгкая серверная санитизация: убрать опасные теги/атрибуты."""
    if not raw:
        return ""
    out = _SCRIPT_RE.sub("", raw)
    out = _EVENT_ATTR_RE.sub("", out)
    out = _JS_URI_RE.sub(r"\1=\2#\2", out)
    return out.strip()


def _plain_text_reply_snippet(raw: Optional[str], max_len: int = 80) -> Optional[str]:
    if raw is None:
        return None
    s = re.sub(r"<[^>]+>", " ", str(raw))
    s = html.unescape(s)
    s = " ".join(s.split())
    if not s:
        return None
    if max_len and len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s or None


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _persist_chat_image(contents: bytes, original_filename: str) -> tuple[str, str, int]:
    """Сохранить изображение в {MEDIA_DIR}/{hex16}.{ext} → (media_url, ext, size)."""
    ext = (Path(original_filename).suffix or "").lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"
    safe_name = f"{uuid.uuid4().hex[:16]}{ext}"
    abs_dir = Path(settings.MEDIA_DIR)
    abs_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_dir / safe_name
    with open(abs_path, "wb") as f:
        f.write(contents)
    media_url = f"/media/{safe_name}"
    return media_url, ext, len(contents)


def _merge_legacy_file_attachment(msg: dict) -> None:
    """Добавить legacy-путь из file_new в attachments для отображения."""
    fp = msg.get("file_path")
    if not fp:
        return
    attachments = msg.setdefault("attachments", [])
    if any(a.get("file_path") == fp for a in attachments):
        return
    ext = Path(fp).suffix
    attachments.append({
        "id": 0,
        "file_path": fp,
        "original_filename": Path(fp).name,
        "file_ext": ext or None,
        "file_size_bytes": None,
        "is_image": _is_image_ext(ext),
    })


def _disk_path_from_media_url(media_url: str) -> Optional[str]:
    if not media_url or not media_url.startswith("/media/"):
        return None
    rel = media_url[len("/media/"):]
    return str(Path(settings.MEDIA_DIR) / rel)


# ─────────────────────────────────────────────────────────────────────────────
# Список чатов
# ─────────────────────────────────────────────────────────────────────────────


def _enrich_chat_dates(chats: List[dict]) -> None:
    for chat in chats:
        chat["last_message_date_iso"] = _iso(chat.pop("last_message_date", None))
        chat.setdefault("top_subscriber_rank", None)


async def get_all_users_chats(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    since_timestamp: Optional[int] = None,
) -> List[dict]:
    where_clauses = ["(ud.\"name\" IS NOT NULL OR u.is_juridical = 2)"]
    params: Dict[str, Any] = {}
    if since_timestamp is not None:
        where_clauses.append("um.date_tz > (to_timestamp(:since_timestamp) AT TIME ZONE 'UTC')")
        params["since_timestamp"] = since_timestamp
    where_clause = " AND ".join(where_clauses)

    limit_clause = ""
    if limit is not None:
        limit_clause += " LIMIT :limit"
        params["limit"] = limit
    if offset is not None:
        limit_clause += " OFFSET :offset"
        params["offset"] = offset

    query = f"""
        WITH latest_messages AS (
            SELECT
                u.id as chat_id,
                CASE
                    WHEN u.is_juridical = 0 THEN INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic)
                    ELSE jcl.short_name_organization
                END AS fullname,
                CASE WHEN sf.station_name IS NULL THEN ig.name ELSE sf.station_name END AS station_name,
                MAX(um.date_tz) AS last_message_date,
                CASE WHEN EXISTS (
                        SELECT 1 FROM radius.radacct r
                        WHERE lower(r.username) = lower(u.login) AND r.acctstoptime IS NULL
                    ) THEN 1 ELSE 0 END AS is_online,
                COALESCE(SUM(um.new), 0) AS unread,
                u.is_juridical,
                (array_agg(um."text" ORDER BY um.date_tz DESC NULLS LAST))[1] AS last_message_text
            FROM users.user_mail um
            LEFT JOIN users.user u ON u.id = um.id_user_from OR u.id = um.id_user_to
            LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp
            LEFT JOIN users.user_details ud ON ud.user_id = u.id
            LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
            LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.jur_id::int
            WHERE {where_clause}
            GROUP BY u.id, ud.surname, ud.name, ud.patronymic, sf.station_name, ig.name,
                     u.login, u.is_juridical, jcl.short_name_organization
        )
        SELECT
            chat_id, fullname, station_name,
            COALESCE(last_message_text, '') AS last_message_text,
            last_message_date, is_online,
            unread AS unread_count,
            CASE WHEN unread > 0 THEN true ELSE false END AS has_unread,
            CASE WHEN is_juridical = 0 THEN false ELSE true END AS is_jur
        FROM latest_messages
        ORDER BY has_unread DESC, last_message_date DESC NULLS LAST
        {limit_clause};
    """
    result = await db.execute(text(query), params)
    chats = [dict(r) for r in result.mappings().all()]
    _enrich_chat_dates(chats)
    return chats


async def search_users_chats(db: AsyncSession, query: str, limit: int) -> List[dict]:
    is_id_search = query.isdigit()
    params: Dict[str, Any] = {"limit": limit}
    base = """
        WITH latest_messages AS (
            SELECT
                u.id as chat_id,
                CASE WHEN u.is_juridical = 0 THEN INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic)
                     ELSE jcl.short_name_organization END AS fullname,
                CASE WHEN sf.station_name IS NULL THEN ig.name ELSE sf.station_name END AS station_name,
                MAX(um.date_tz) AS last_message_date,
                (array_agg(um."text" ORDER BY um.date_tz DESC NULLS LAST))[1] AS last_message_text,
                COALESCE(SUM(um.new), 0) AS unread,
                u.is_juridical,
                CASE WHEN EXISTS (
                        SELECT 1 FROM radius.radacct r
                        WHERE lower(r.username) = lower(u.login) AND r.acctstoptime IS NULL
                    ) THEN 1 ELSE 0 END AS is_online
            FROM users.user_mail um
            LEFT JOIN users.user u ON u.id = um.id_user_from OR u.id = um.id_user_to
            LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp
            LEFT JOIN users.user_details ud ON ud.user_id = u.id
            LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
            LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.jur_id::int
            WHERE (ud."name" IS NOT NULL OR u.is_juridical = 2) AND {cond}
            GROUP BY u.id, ud.surname, ud.name, ud.patronymic, sf.station_name, ig.name,
                     u.login, u.is_juridical, jcl.short_name_organization
        )
        SELECT chat_id, fullname, station_name,
               COALESCE(last_message_text, '') AS last_message_text,
               last_message_date, is_online,
               unread AS unread_count,
               CASE WHEN unread > 0 THEN true ELSE false END AS has_unread,
               CASE WHEN is_juridical = 0 THEN false ELSE true END AS is_jur
        FROM latest_messages
        ORDER BY has_unread DESC, last_message_date DESC NULLS LAST
        LIMIT :limit;
    """
    if is_id_search:
        sql = base.format(cond="u.id = :search_id")
        params["search_id"] = int(query)
    else:
        sql = base.format(cond=(
            "(LOWER(INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic)) LIKE LOWER(:q)"
            " OR LOWER(ud.surname) LIKE LOWER(:q) OR LOWER(ud.name) LIKE LOWER(:q)"
            " OR LOWER(jcl.short_name_organization) LIKE LOWER(:q))"
        ))
        params["q"] = f"%{query}%"
    result = await db.execute(text(sql), params)
    chats = [dict(r) for r in result.mappings().all()]
    _enrich_chat_dates(chats)
    return chats


async def find_or_create_chat(db: AsyncSession, user_id: int) -> Optional[dict]:
    row = await db.execute(
        text("""
            SELECT
                u.id AS chat_id,
                CASE WHEN u.is_juridical = 0 THEN INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic)
                     ELSE jcl.short_name_organization END AS fullname,
                CASE WHEN sf.station_name IS NULL THEN ig.name ELSE sf.station_name END AS station_name,
                u.is_juridical,
                CASE WHEN EXISTS (
                        SELECT 1 FROM radius.radacct r
                        WHERE lower(r.username) = lower(u.login) AND r.acctstoptime IS NULL
                    ) THEN 1 ELSE 0 END AS is_online
            FROM users.user u
            LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp
            LEFT JOIN users.user_details ud ON ud.user_id = u.id
            LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
            LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.jur_id::int
            WHERE u.id = :uid
            LIMIT 1
        """),
        {"uid": user_id},
    )
    rec = row.mappings().first()
    if not rec:
        return None
    return {
        "chat_id": user_id,
        "fullname": (rec.get("fullname") or "").strip() or f"Пользователь #{user_id}",
        "station_name": rec.get("station_name") or "",
        "last_message_text": "",
        "last_message_date_iso": None,
        "is_online": rec.get("is_online") or 0,
        "unread_count": 0,
        "has_unread": False,
        "is_jur": (rec.get("is_juridical") or 0) != 0,
        "top_subscriber_rank": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Сообщения
# ─────────────────────────────────────────────────────────────────────────────

_MESSAGE_SELECT = """
    SELECT
        um.id AS msg_id,
        um.date_tz AS date_ts,
        um."text",
        CASE WHEN um.file_new IS NULL OR um.file_new = '0' OR um.file_new = '' THEN NULL ELSE um.file_new END AS file_path,
        CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
             THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
             ELSE um.answer END AS answer,
        CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
             THEN CASE WHEN um.person_type = 'skystream' AND um.user_id = :user_id THEN 'Вы'
                       WHEN um.person_type = 'skystream' AND au_author.role = 'engineer' THEN 'Инженер'
                       WHEN um.person_type = 'skystream' AND au_author.role = 'support' THEN COALESCE(au_author.full_name, 'Поддержка')
                       WHEN um.person_type = 'skystream' THEN 'Партнёр'
                       WHEN um.person_type = 'user' THEN 'Абонент'
                       ELSE 'Партнёр' END
             ELSE CASE WHEN um.id_user_from = 2 THEN 'Контактный сервис'
                       WHEN um.id_user_from = :chat_id THEN 'Пользователь'
                       WHEN um.id_user_from = :user_id THEN 'Вы'
                       WHEN au.role = 'engineer' THEN 'Инженер'
                       WHEN au.role = 'support' THEN au.full_name
                       WHEN au.id IS NOT NULL THEN 'Партнёр'
                       ELSE 'Неизвестный отправитель' END END AS whose_message,
        CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
             THEN CASE WHEN um.person_type = 'user' THEN 'subscriber'
                       WHEN um.person_type = 'skystream' AND au_author.role = 'engineer' THEN 'engineer'
                       WHEN um.person_type = 'skystream' AND au_author.role = 'support' THEN 'support'
                       WHEN um.person_type = 'skystream' THEN 'partner'
                       ELSE 'partner' END
             ELSE CASE WHEN um.id_user_from = :chat_id THEN 'subscriber'
                       WHEN au.role = 'engineer' THEN 'engineer'
                       WHEN au.role = 'support' THEN 'support'
                       WHEN au.id IS NOT NULL THEN 'partner'
                       ELSE 'support' END END AS author_kind,
        ((EXISTS (SELECT 1 FROM users.user_mail_reads r WHERE r.msg_id = um.id AND r.user_id <> COALESCE(um.user_id, um.id_user_from)))
         OR ((NOT (EXISTS (SELECT 1 FROM users.user_mail_reads r2 WHERE r2.msg_id = um.id))) AND (TRIM(COALESCE(um."read"::text, '0')) = '1'))
         OR (um.date_tz < '2026-01-01'::timestamptz)) AS has_read,
        (EXISTS (SELECT 1 FROM users.user_mail_reads r WHERE r.msg_id = um.id)) AS read_from_table,
        (SELECT r.read_time FROM users.user_mail_reads r WHERE r.msg_id = um.id AND r.person_type = 'user' ORDER BY r.read_time ASC LIMIT 1) AS subscriber_read_at,
        TRIM(COALESCE(um."read"::text, '0')) AS legacy_read,
        COALESCE(um.user_id, um.id_user_from) AS user_id,
        um.relay_msg_id,
        LEFT(um2."text", :relay_snippet_raw_max) AS relay_snippet,
        CASE WHEN um2.id IS NULL THEN NULL WHEN um2.id_user_from = 2 THEN 'Контактный сервис'
            WHEN um2.id_user_from = :chat_id THEN 'Пользователь' WHEN um2.id_user_from = :user_id THEN 'Вы'
            WHEN au2.role = 'engineer' THEN 'Инженер'
            WHEN au2.role = 'support' THEN au2.full_name
            WHEN au2.id IS NOT NULL THEN 'Партнёр' ELSE 'Неизвестный' END AS relay_author
    FROM users.user_mail um
    LEFT JOIN users.skystream_users au ON au.id = um.id_user_from
    LEFT JOIN users.skystream_users au_author ON au_author.id = um.user_id AND um.person_type = 'skystream'
    LEFT JOIN users.skystream_users au_bot ON au_bot.id = um.user_id AND um.person_type = 'bot'
    LEFT JOIN partner.diler d_author ON d_author.id = um.user_id AND um.person_type = 'partner'
    LEFT JOIN partner.technicians t_author ON t_author.technician_id = um.user_id AND um.person_type = 'tech'
    LEFT JOIN users.user_mail um2 ON um2.id = NULLIF(trim(COALESCE(um.relay_msg_id, '')), '')::bigint
    LEFT JOIN users.skystream_users au2 ON au2.id = um2.id_user_from
"""


def _row_to_message(row: dict) -> dict:
    d = dict(row)
    d["date_iso"] = _iso(d.pop("date_ts", None))
    d["whose_message"] = d.get("whose_message") or "—"
    d["answer"] = bool(d.get("answer"))
    sub_read = d.get("subscriber_read_at")
    d["subscriber_read_at"] = sub_read.isoformat() if hasattr(sub_read, "isoformat") else (sub_read or None)
    from_table = d.pop("read_from_table", None) in (True, 1)
    legacy_one = str(d.pop("legacy_read", "") or "").strip() == "1"
    v = d.get("has_read")
    d["has_read"] = True if (not from_table and legacy_one) else (v is True or v == 1)
    rs = d.get("relay_snippet")
    if rs is not None:
        d["relay_snippet"] = _plain_text_reply_snippet(rs)
    return d


async def _attachments_for(db: AsyncSession, msg_ids: List[int]) -> Dict[int, list]:
    if not msg_ids:
        return {}
    result = await db.execute(
        select(UserMailAttachment).where(UserMailAttachment.msg_id.in_(msg_ids))
    )
    out: Dict[int, list] = {mid: [] for mid in msg_ids}
    for r in result.scalars().all():
        out.setdefault(r.msg_id, []).append({
            "id": r.id,
            "file_path": r.file_path,
            "original_filename": r.original_filename,
            "file_ext": r.file_ext,
            "file_size_bytes": r.file_size_bytes,
            "is_image": _is_image_ext(r.file_ext or Path(r.original_filename or "").suffix),
        })
    return out


async def get_users_messages(
    db: AsyncSession,
    chat_id: int,
    operator: dict,
    limit: int = 20,
    offset: int = 0,
    after_id: Optional[int] = None,
    before_id: Optional[int] = None,
) -> List[dict]:
    where = ("WHERE (um.user_chat = :chat_id OR (um.user_chat IS NULL "
             "AND (um.id_user_from = :chat_id OR um.id_user_to = :chat_id)))")
    params: Dict[str, Any] = {
        "chat_id": chat_id,
        "user_id": operator["user_id"],
        "role": operator.get("role"),
        "limit": limit,
        "offset": offset,
        "relay_snippet_raw_max": _RELAY_SNIPPET_RAW_MAX,
    }
    if before_id is not None:
        where += " AND um.id < :before_id"
        params["before_id"] = before_id
    if after_id is not None:
        where += " AND um.id > :after_id"
        params["after_id"] = after_id

    if after_id is not None:
        order = "ORDER BY um.id ASC LIMIT :limit"
    elif before_id is not None:
        order = "ORDER BY um.id DESC LIMIT :limit OFFSET 0"
    else:
        order = "ORDER BY um.id DESC LIMIT :limit OFFSET :offset"

    result = await db.execute(text(f"{_MESSAGE_SELECT}\n{where}\n{order}"), params)
    messages = [_row_to_message(dict(r)) for r in result.mappings().all()]
    att = await _attachments_for(db, [m["msg_id"] for m in messages])
    for m in messages:
        m["attachments"] = att.get(m["msg_id"], [])
        _merge_legacy_file_attachment(m)
    return messages


async def mark_as_read(
    db: AsyncSession,
    message_ids: List[int],
    reader_user_id: int,
    person_type: str = "skystream",
) -> dict:
    if not message_ids:
        return {"status": "ok", "marked": 0}
    await db.execute(
        text("UPDATE users.user_mail SET new = 0, read = '1' WHERE id = ANY(:ids) AND id_user_to = :rid"),
        {"ids": message_ids, "rid": reader_user_id},
    )
    await db.execute(
        text(f"UPDATE users.user_mail SET new = 0 WHERE id = ANY(:ids) AND id_user_from > {_SUBSCRIBER_ID_THRESHOLD}"),
        {"ids": message_ids},
    )
    for msg_id in message_ids:
        await db.execute(
            text("""
                INSERT INTO users.user_mail_reads (msg_id, user_id, person_type)
                VALUES (:msg_id, :user_id, :person_type)
                ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
            """),
            {"msg_id": msg_id, "user_id": reader_user_id, "person_type": person_type},
        )
    await db.commit()
    return {"status": "ok", "marked": len(message_ids)}


async def get_messages_reads_batch(db: AsyncSession, msg_ids: List[int]) -> dict:
    if not msg_ids:
        return {}
    ids = ", ".join(str(int(i)) for i in msg_ids)
    result = await db.execute(text(f"""
        SELECT r.msg_id, r.read_time, r.person_type, r.user_id,
            COALESCE(
                CASE WHEN r.person_type = 'skystream' THEN au.full_name END,
                CASE WHEN r.person_type = 'partner' THEN d.fullname END,
                CASE WHEN r.person_type = 'user' THEN 'Абонент' END,
                CASE WHEN r.person_type = 'tech' THEN t.full_name END,
                'Пользователь #' || r.user_id::text
            ) AS display_name
        FROM users.user_mail_reads r
        LEFT JOIN users.skystream_users au ON au.id = r.user_id AND r.person_type = 'skystream'
        LEFT JOIN partner.diler d ON d.id = r.user_id AND r.person_type = 'partner'
        LEFT JOIN partner.technicians t ON t.technician_id = r.user_id AND r.person_type = 'tech'
        WHERE r.msg_id IN ({ids})
        ORDER BY r.read_time ASC
    """))
    out: Dict[int, list] = {mid: [] for mid in msg_ids}
    for r in result.mappings().all():
        rt = r.get("read_time")
        out.setdefault(r["msg_id"], []).append({
            "label": (r.get("display_name") or "—").strip() or "—",
            "read_at_iso": rt.isoformat() if hasattr(rt, "isoformat") else str(rt or ""),
            "person_type": r.get("person_type"),
        })
    return out


async def get_number_unread_chats(db: AsyncSession, role: Optional[str]) -> dict:
    line = 1 if role == "support" else 2
    result = await db.execute(
        text(f"""
            SELECT
                (SELECT COUNT(DISTINCT CASE WHEN id_user_from > {_SUBSCRIBER_ID_THRESHOLD} THEN id_user_from ELSE id_user_to END)
                 FROM users.user_mail WHERE "new" = 1) AS opened_chats,
                (SELECT COUNT(1) FROM users.tracker_tickets
                 WHERE support_line = :line AND status IN ('pending', 'in_progress')) AS opened_trackers
        """),
        {"line": line},
    )
    row = result.mappings().first()
    return dict(row) if row else {"opened_chats": 0, "opened_trackers": 0}


# ─────────────────────────────────────────────────────────────────────────────
# Эндпоинты: список чатов
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/all")
async def list_chats(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_tracker_user),
):
    return await get_all_users_chats(db, limit=limit, offset=offset)


@router.get("/updates")
async def chat_updates(
    last_sync: float = Query(0),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_tracker_user),
):
    if not last_sync or math.isnan(last_sync):
        return []
    return await get_all_users_chats(db, since_timestamp=int(last_sync))


@router.get("/search")
async def search_chats(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_tracker_user),
):
    return await search_users_chats(db, query.strip(), limit)


@router.get("/find-or-create")
async def find_or_create(
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_tracker_user),
):
    chat = await find_or_create_chat(db, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    return chat


@router.get("/unread_chats")
async def unread_chats(
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    uid = int(user["user_id"])
    cache_key = f"chat_unread:{uid}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    result = await get_number_unread_chats(db, user.get("role"))
    try:
        await redis_client.setex(cache_key, _UNREAD_CACHE_TTL, json.dumps(result))
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Эндпоинты: сообщения
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{chat_id}/messages")
async def chat_messages(
    chat_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_id: Optional[int] = Query(None, ge=1),
    after_id: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    messages = await get_users_messages(
        db, chat_id, _operator(user),
        limit=limit, offset=offset, before_id=before_id, after_id=after_id,
    )
    return {"messages": messages, "has_older": len(messages) >= limit and after_id is None}


@router.get("/{chat_id}/messages/updates")
async def chat_messages_updates(
    chat_id: int,
    after_id: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    if after_id <= 0:
        return {"messages": []}
    messages = await get_users_messages(
        db, chat_id, _operator(user), limit=50, after_id=after_id,
    )
    return {"messages": messages}


@router.get("/{chat_id}/messages/reads")
async def chat_messages_reads(
    chat_id: int,
    msg_ids: str = Query(""),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_tracker_user),
):
    ids = [int(x) for x in msg_ids.split(",") if x.strip().isdigit()][:200]
    return {"read_by_receipts": await get_messages_reads_batch(db, ids)}


@router.post("/{chat_id}/messages")
async def create_message(
    chat_id: int,
    request: Request,
    text_field: str = Form("", alias="text"),
    file: Optional[UploadFile] = File(None),
    reply_to_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    operator = _operator(user)
    has_file = file is not None and bool(file.filename)
    has_text = bool(html_to_plain_text(text_field))
    if has_text and has_file:
        raise HTTPException(
            status_code=400,
            detail="Отправьте текст или изображение, но не оба одновременно.",
        )
    if not has_text and not has_file:
        raise HTTPException(
            status_code=400,
            detail="Нельзя отправить пустое сообщение. Добавьте текст или изображение.",
        )

    clean_text = _sanitize_html(text_field) if has_text else ""
    relay = None
    if reply_to_id and str(reply_to_id).strip().isdigit():
        relay = str(int(reply_to_id))

    file_new_path = ""
    real_file = None
    if has_file:
        file_bytes = await file.read()
        file_orig = file.filename or "image"
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Разрешены только изображения")
        if len(file_bytes) > MAX_ATTACHMENT_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="Изображение больше 15 МБ")
        ext = (Path(file_orig).suffix or "").lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Разрешены только изображения (JPG, PNG, GIF, WebP, BMP)")
        if not _check_image_magic(file_bytes, ext):
            raise HTTPException(status_code=400, detail="Содержимое файла не соответствует типу изображения")
        file_new_path, _, _ = _persist_chat_image(file_bytes, file_orig)
        real_file = file_orig

    msg = UserMail(
        text_=clean_text,
        id_user_from=operator["user_id"],
        id_user_to=chat_id,
        read="0",
        answer=1,
        new=0,
        date=int(datetime.now(timezone.utc).timestamp()),
        file_new=file_new_path,
        real_file=real_file,
        ip_address=_client_ip(request),
        user_id=operator["user_id"],
        person_type="skystream",
        user_chat=chat_id,
        relay_msg_id=relay,
    )
    db.add(msg)
    await db.flush()
    msg_id = msg.id

    attachments: List[dict] = []
    if file_new_path:
        ext = Path(file_new_path).suffix
        attachments.append({
            "id": 0,
            "file_path": file_new_path,
            "original_filename": real_file or Path(file_new_path).name,
            "file_ext": ext or None,
            "file_size_bytes": None,
            "is_image": True,
        })

    await db.commit()

    return {
        "msg_id": msg_id,
        "date_iso": datetime.now(timezone.utc).isoformat(),
        "text": clean_text,
        "file_path": file_new_path or None,
        "answer": True,
        "whose_message": "Вы",
        "author_kind": (
            "engineer" if operator.get("role") == "engineer"
            else "support" if operator.get("role") == "support"
            else "partner"
        ),
        "has_read": False,
        "user_id": operator["user_id"],
        "subscriber_read_at": None,
        "relay_msg_id": relay,
        "relay_author": None,
        "relay_snippet": None,
        "attachments": attachments,
    }


@router.post("/{chat_id}/messages/read")
async def mark_messages_read(
    chat_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    raw_ids = payload.get("message_ids") or []
    ids = [int(x) for x in raw_ids if str(x).strip().lstrip("-").isdigit()]
    person_type = payload.get("person_type") or "skystream"
    result = await mark_as_read(db, ids, int(user["user_id"]), person_type)
    try:
        await redis_client.delete(f"chat_unread:{int(user['user_id'])}")
    except Exception:
        pass
    return result


@router.put("/{chat_id}/messages/{msg_id}")
async def edit_message(
    chat_id: int,
    msg_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    new_text = _sanitize_html(str(payload.get("text", "")))
    if not html_to_plain_text(new_text):
        raise HTTPException(status_code=400, detail="Текст сообщения не может быть пустым")
    row = await db.execute(
        select(UserMail).where(
            UserMail.id == msg_id,
            UserMail.user_id == int(user["user_id"]),
            or_(
                UserMail.user_chat == chat_id,
                (UserMail.user_chat.is_(None)) & (
                    (UserMail.id_user_from == chat_id) | (UserMail.id_user_to == chat_id)
                ),
            ),
        )
    )
    msg = row.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    msg.text_ = new_text
    msg.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return True


@router.delete("/{chat_id}/messages/{msg_id}")
async def delete_message(
    chat_id: int,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_tracker_user),
):
    row = await db.execute(
        select(UserMail).where(
            UserMail.id == msg_id,
            UserMail.user_id == int(user["user_id"]),
            or_(
                UserMail.user_chat == chat_id,
                (UserMail.user_chat.is_(None)) & (
                    (UserMail.id_user_from == chat_id) | (UserMail.id_user_to == chat_id)
                ),
            ),
        )
    )
    msg = row.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    legacy_path = (msg.file_new or "").strip()
    if legacy_path and legacy_path not in ("0", ""):
        disk = _disk_path_from_media_url(legacy_path)
        if disk and os.path.isfile(disk):
            try:
                os.unlink(disk)
            except OSError:
                logger.warning("delete_message: не удалось удалить файл %s", disk)
    # Удаляем файлы вложений с диска (legacy user_mail_attachments)
    att_rows = await db.execute(
        select(UserMailAttachment).where(UserMailAttachment.msg_id == msg_id)
    )
    for att in att_rows.scalars().all():
        disk = _disk_path_from_media_url(att.file_path or "")
        if disk and os.path.isfile(disk):
            try:
                os.unlink(disk)
            except OSError:
                logger.warning("delete_message: не удалось удалить файл %s", disk)
    await db.delete(msg)
    await db.commit()
    return {"status": "deleted"}
