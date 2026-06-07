

from datetime import datetime, timezone
import html
import io
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, UploadFile
import pytz
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1.routers.helpdesk.dao import UserMailDAO, UserMailAttachmentDAO
from app.models.users import UserMailAttachment
from app.api.v1.routers.helpdesk.user_short_info_in_chat import get_user_short_info
from app.api.v1.routers.users.dao import TopActiveSubscriberDAO
from app.api.v1.routers.helpdesk.chat_files import (
    disk_path_from_media_url,
    persist_chat_file_bytes,
    read_upload_file,
    resolve_mail_storage_scope,
)
from app.config import MEDIA_DIR
from app.database import async_session_maker
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
logger = logging.getLogger("abs")

# Сырой фрагмент цитируемого текста из БД (часто HTML); обрезаем побольше, plain — в Python
_RELAY_SNIPPET_RAW_MAX = 800
MAX_ATTACHMENT_SIZE_BYTES = 15 * 1024 * 1024  # 15 МБ на файл


def _plain_text_reply_snippet(raw: Optional[str], max_len: int = 80) -> Optional[str]:
    """Превью «ответ на»: убрать HTML, сущности → текст, обрезка для одной строки в UI."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = " ".join(s.split())
    if max_len and len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s or None

# PDF, Excel, Word, CSV и изображения
ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".docm", ".csv",
}

# Сигнатуры по началу файла (magic bytes): защита от подмены расширения (например .exe как .pdf)
_MAGIC_SIGNATURES = [
    (b"%PDF", [".pdf"]),
    (b"\xff\xd8\xff", [".jpg", ".jpeg"]),
    (b"\x89PNG\r\n\x1a\n", [".png"]),
    (b"GIF87a", [".gif"]),
    (b"GIF89a", [".gif"]),
    (b"BM", [".bmp"]),
    (b"RIFF", [".webp"]),  # WebP: RIFF....WEBP, проверим WEBP ниже
    (b"PK\x03\x04", [".xlsx", ".docx", ".docm"]),  # Office 2007+ (ZIP) — дополнительно проверяем OOXML
    (b"\xd0\xcf\x11\xe0", [".xls", ".doc"]),  # OLE (старые Office)
]


def _check_file_magic(contents: bytes, ext: str) -> bool:
    """
    Проверяет, что содержимое соответствует заявленному расширению по началу файла (magic bytes).
    Защита от загрузки вредоносных файлов под видом легитимных (например .exe с расширением .pdf).
    """
    if len(contents) < 12:
        return False
    ext = ext.lower()
    if ext == ".csv":
        # CSV: текстовый формат, без null-байтов и без явно бинарных паттернов
        sample = contents[:2048]
        if b"\x00" in sample:
            return False
        printable = sum(1 for b in sample if b in (9, 10, 13, 32) or 32 <= b < 127 or b >= 0xC0)
        if len(sample) and printable / len(sample) < 0.7:
            return False
        return True
    if ext == ".webp":
        if not contents.startswith(b"RIFF") or len(contents) < 12:
            return False
        return contents[8:12] == b"WEBP"
    # Office 2007+ (ZIP): требуем структуру OOXML — наличие [Content_Types].xml (есть в любом .docx/.xlsx)
    if ext in (".docx", ".docm", ".xlsx") and contents.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(contents), "r") as zf:
                names = zf.namelist()
                if "[Content_Types].xml" not in names:
                    return False
                # Дополнительно: для Word — word/document.xml или word/document2.xml; для Excel — xl/workbook.xml
                if ext.startswith(".doc"):
                    if not any(n.startswith("word/") for n in names):
                        return False
                elif ext in (".xlsx",):
                    if not any(n.startswith("xl/") for n in names):
                        return False
        except (zipfile.BadZipFile, KeyError, OSError):
            return False
        return True
    for magic, exts in _MAGIC_SIGNATURES:
        if ext not in exts:
            continue
        if magic == b"RIFF":
            continue  # WebP обработан выше
        if magic == b"PK\x03\x04":
            continue  # OOXML обработан выше
        if contents.startswith(magic):
            return True
    return False

# -----------------------------------------------------------------------------------------------------------------
# Вспомогательные утилиты (без БД) — остаются как есть
# -----------------------------------------------------------------------------------------------------------------

def get_moscow_timestamp() -> Tuple[int, str]:
    """Получение текущего времени в Москве (timestamp и отформатированная строка)."""
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    moscow_timestamp = int(moscow_time.timestamp())
    formatted_time = moscow_time.strftime("%Y-%m-%d %H:%M")
    logger.debug(f"Moscow timestamp: {moscow_timestamp}, formatted: {formatted_time}")
    return moscow_timestamp, formatted_time


async def process_form_data(form: dict) -> Tuple[str, Optional[UploadFile]]:
    """Парсинг multipart/form-data для получения текста и файла."""
    text = form.get("text", "")
    file = form.get("file")
    logger.debug(f"Form data: text='{text[:50]}...', file={file.filename if file else None}")
    return text, file


async def process_uploaded_image(
    file: UploadFile,
    storage_user_id: int,
    storage_scope_id: int,
    timestamp: int,
) -> tuple[str, str]:
    """
    Устаревший контракт (optimized_url, raw_url) для совместимости.
    Файл сохраняется в /media/chat/{user_id}/{ticket_id}/…; оба URL указывают на него.
    """
    contents, orig_name = await read_upload_file(file)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Только изображения разрешены")
    ext = (Path(orig_name).suffix or "").lower()
    if ext and ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")
    if ext and not _check_file_magic(contents, ext):
        raise HTTPException(status_code=400, detail="Содержимое файла не соответствует типу")
    file_path, _, _ = persist_chat_file_bytes(
        contents,
        orig_name,
        storage_user_id=storage_user_id,
        storage_scope_id=storage_scope_id,
        timestamp=timestamp,
    )
    return file_path, file_path


def create_response(
    msg_id: int,
    text: str,
    file_path: str | None,
    formatted_time: str,
    user_id: int,
    relay_msg_id: Optional[str] = None,
    relay_author: Optional[str] = None,
    relay_snippet: Optional[str] = None,
) -> dict:
    utc_now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {
        "msg_id": msg_id,
        "text": text,
        "file_path": file_path,
        "date": utc_now_iso,
        "answer": 1,
        "whose_message": "Вы",
        "has_read": False,
        "user_id": user_id,
    }
    if relay_msg_id:
        out["relay_msg_id"] = relay_msg_id
        if relay_author is not None:
            out["relay_author"] = relay_author
        if relay_snippet is not None:
            out["relay_snippet"] = relay_snippet
    return out


async def save_chat_attachment(
    db: AsyncSession,
    msg_id: int,
    chat_id: int,
    file: UploadFile,
    *,
    ticket_id: Optional[int] = None,
    timestamp: Optional[int] = None,
) -> dict:
    """Сохранить вложение в user_mail_attachments: /media/chat/{user_id}/{ticket_id}/…"""
    contents, original_filename = await read_upload_file(file)
    ext = (Path(original_filename).suffix or "").lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Разрешены только: изображения (JPG, PNG, GIF, WebP, BMP), PDF, Word (DOC, DOCX), Excel (XLS, XLSX), CSV.",
        )
    if not _check_file_magic(contents, ext):
        raise HTTPException(
            status_code=400,
            detail="Содержимое файла не соответствует заявленному типу. Возможна подмена расширения — загрузите файл в нужном формате.",
        )
    storage_user_id, storage_scope_id = await resolve_mail_storage_scope(
        db, chat_id=chat_id, msg_id=msg_id, ticket_id=ticket_id,
    )
    file_path, file_ext, file_size = persist_chat_file_bytes(
        contents,
        original_filename,
        storage_user_id=storage_user_id,
        storage_scope_id=storage_scope_id,
        timestamp=timestamp,
    )
    row = await UserMailAttachmentDAO.add(
        db,
        msg_id=msg_id,
        file_path=file_path,
        original_filename=original_filename,
        file_ext=file_ext or None,
        file_size_bytes=file_size,
    )
    return {
        "id": row["id"],
        "msg_id": msg_id,
        "file_path": file_path,
        "original_filename": original_filename,
        "file_ext": file_ext or None,
        "file_size_bytes": file_size,
    }


async def save_mail_prepared_attachments(
    db: AsyncSession,
    *,
    msg_id: int,
    chat_id: int,
    prepared: list,
    ticket_id: Optional[int] = None,
    timestamp: Optional[int] = None,
    commit: bool = False,
) -> List[dict]:
    """Записать уже прочитанные файлы (PreparedChatFile) к mail-сообщению.

    Для двухфазной отправки: вызывается ДО commit, чтобы сообщение и вложения
    зафиксировались в одной транзакции (другие проекты не видят пустое сообщение).
    При ошибке откатывает транзакцию и чистит уже записанные на диск файлы.
    """
    if not prepared:
        return []

    storage_user_id, storage_scope_id = await resolve_mail_storage_scope(
        db, chat_id=chat_id, msg_id=msg_id, ticket_id=ticket_id,
    )
    saved_disk_paths: List[str] = []
    records: List[dict] = []
    try:
        for item in prepared:
            file_path, file_ext, file_size = persist_chat_file_bytes(
                item.contents,
                item.original_filename,
                storage_user_id=storage_user_id,
                storage_scope_id=storage_scope_id,
                timestamp=timestamp,
            )
            saved_disk_paths.append(file_path)
            row = await UserMailAttachmentDAO.add(
                db,
                auto_commit=False,
                msg_id=msg_id,
                file_path=file_path,
                original_filename=item.original_filename,
                file_ext=file_ext or None,
                file_size_bytes=file_size,
            )
            records.append({
                "id": row["id"],
                "msg_id": msg_id,
                "file_path": file_path,
                "original_filename": item.original_filename,
                "file_ext": file_ext or None,
                "file_size_bytes": file_size,
            })
        if commit:
            await db.commit()
        return records
    except Exception:
        await db.rollback()
        for fp in saved_disk_paths:
            disk = disk_path_from_media_url(fp)
            if disk and os.path.isfile(disk):
                try:
                    os.unlink(disk)
                except OSError:
                    logger.warning("mail attachment cleanup failed: %s", disk)
        raise


async def get_attachments_for_messages(
    db: AsyncSession,
    msg_ids: List[int],
) -> dict:
    """Возвращает словарь msg_id -> список словарей вложений."""
    if not msg_ids:
        return {}
    stmt = select(UserMailAttachment).where(UserMailAttachment.msg_id.in_(msg_ids))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    out = {mid: [] for mid in msg_ids}
    for r in rows:
        out[r.msg_id].append({
            "id": r.id,
            "file_path": r.file_path,
            "original_filename": r.original_filename,
            "file_ext": r.file_ext,
            "file_size_bytes": r.file_size_bytes,
        })
    return out


async def resolve_mail_attachment_download(
    db: AsyncSession,
    *,
    attachment_id: int,
    chat_id: int,
) -> tuple[str, str, str]:
    """Путь на диске, original_filename, media_type для скачивания вложения user_mail."""
    import mimetypes
    from app.models.users import UserMail
    from sqlalchemy import or_

    row = await UserMailAttachmentDAO.find_one_or_none(db, id=attachment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Вложение не найдено")

    msg_id = row.get("msg_id")
    check = await db.execute(
        select(UserMail.id).where(
            UserMail.id == msg_id,
            or_(
                UserMail.user_chat == chat_id,
                (UserMail.user_chat.is_(None)) & (
                    (UserMail.id_user_from == chat_id) | (UserMail.id_user_to == chat_id)
                ),
            ),
        ).limit(1)
    )
    if not check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Вложение не найдено в этом чате")

    disk = disk_path_from_media_url(row.get("file_path") or "")
    if not disk or not os.path.isfile(disk):
        raise HTTPException(status_code=404, detail="Файл не найден на сервере")

    filename = (row.get("original_filename") or os.path.basename(disk) or "file")[:512]
    ext = (row.get("file_ext") or Path(filename).suffix or "").lower()
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    guessed, _ = mimetypes.guess_type(f"name{ext}")
    return disk, filename, guessed or "application/octet-stream"


async def delete_chat_attachment(
    db: AsyncSession,
    attachment_id: int,
    msg_id: int,
    chat_id: int,
) -> bool:
    """Удалить вложение: файл с диска и запись в user_mail_attachments. Проверяет, что сообщение принадлежит чату."""
    from app.models.users import UserMail
    from sqlalchemy import or_
    check = await db.execute(
        select(UserMail.id).where(
            UserMail.id == msg_id,
            or_(
                UserMail.user_chat == chat_id,
                (UserMail.user_chat.is_(None)) & (
                    (UserMail.id_user_from == chat_id) | (UserMail.id_user_to == chat_id)
                ),
            ),
        ).limit(1)
    )
    if not check.scalar_one_or_none():
        return False
    row = await UserMailAttachmentDAO.find_one_or_none(db, id=attachment_id, msg_id=msg_id)
    if not row:
        return False
    disk_path = disk_path_from_media_url(row.get("file_path") or "")
    if disk_path and os.path.isfile(disk_path):
        try:
            os.unlink(disk_path)
        except OSError:
            logger.warning("delete_chat_attachment: не удалось удалить файл %s", disk_path)
    await UserMailAttachmentDAO.delete(db, id=attachment_id, msg_id=msg_id)
    return True


# -----------------------------------------------------------------------------------------------------------------
# Функции работы с БД — принимают session: AsyncSession
# -----------------------------------------------------------------------------------------------------------------

async def save_message_to_db(
    db: AsyncSession,
    chat_id: int,
    user_id: int,
    text: str,
    file_path: str,
    real_file: str,
    client_ip: str,
    relay_msg_id: Optional[str] = None,
    ticket_id: Optional[int] = None,
    auto_commit: bool = True,
) -> int:
    """Сохранение сообщения в БД. date_tz — server default now(). ticket_id — ID тикета, если сообщение из чата тикета.

    auto_commit=False — для двухфазной отправки: сообщение + вложения пишутся в
    одной транзакции (commit делает вызывающий код).
    """
    moscow_ts, _ = get_moscow_timestamp()
    kwargs = dict(
        text_=text,
        id_user_from=user_id,
        id_user_to=chat_id,
        read='0',
        answer=1,
        date=moscow_ts,
        file_new=file_path or '',
        real_file=real_file or None,
        ip_address=client_ip,
        user_id=user_id,
        person_type='skystream',
        user_chat=chat_id,
    )
    if relay_msg_id is not None:
        kwargs['relay_msg_id'] = relay_msg_id
    if ticket_id is not None:
        kwargs['ticket_id'] = ticket_id
    msg_id = await UserMailDAO.add(db, auto_commit=auto_commit, **kwargs)
    logger.info(f"Successfully created message msg_id={msg_id} in chat with user {chat_id} by partner {user_id}")
    return msg_id


async def get_all_users_chats(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    since_timestamp: Optional[int] = None
) -> List[dict]:
    """Получение списка чатов (все или только обновлённые)."""

    # Базовая часть WHERE
    where_clauses = ["(ud.\"name\" IS NOT NULL OR u.is_juridical = 2)"]
    params = {}

    if since_timestamp is not None:
        where_clauses.append("um.date_tz > (to_timestamp(:since_timestamp) AT TIME ZONE 'UTC')")
        params["since_timestamp"] = since_timestamp

    where_clause = " AND ".join(where_clauses)

    # Формируем LIMIT/OFFSET часть
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
                CASE
                    WHEN sf.station_name IS NULL THEN ig.name
                    ELSE sf.station_name
                END AS station_name,
                MAX(um.date_tz) AS last_message_date,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM radius.radacct r
                        WHERE lower(r.username) = lower(u.login)
                          AND r.acctstoptime IS NULL
                    ) THEN 1
                    ELSE 0
                END AS is_online,
                COALESCE(SUM(um.new), 0) AS unread,
                u.is_juridical,
                (array_agg(um."text" ORDER BY um.date_tz DESC NULLS LAST))[1] AS last_message_text
            FROM users.user_mail um
            LEFT JOIN users.user u
                ON u.id = um.id_user_from OR u.id = um.id_user_to
            LEFT JOIN wifitochka.ip_group ig
                ON ig.id = u.id_grp
            LEFT JOIN users.user_details ud
                ON ud.user_id = u.id
            LEFT JOIN stations.station_forms sf
                ON sf.station_id = ig.id
            LEFT JOIN oss.jur_client_list jcl
                ON jcl.id = u.jur_id::int
            WHERE {where_clause}
            GROUP BY u.id, ud.surname, ud.name, ud.patronymic, sf.station_name, ig.name,
                     u.login, u.is_juridical, jcl.short_name_organization
        )
        SELECT
            chat_id,
            fullname,
            station_name,
            COALESCE(last_message_text, '') AS last_message_text,
            last_message_date,
            is_online,
            unread AS unread_count,
            CASE WHEN unread > 0 THEN true ELSE false END AS has_unread,
            CASE WHEN is_juridical = 0 THEN false ELSE true END AS is_jur
        FROM latest_messages
        ORDER BY has_unread DESC, last_message_date DESC NULLS LAST
        {limit_clause};
    """
    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    chats = [dict(row) for row in rows]
    _enrich_chats_with_dates_and_rank(chats)
    await _enrich_chats_with_top_rank(db, chats)
    return chats


def _enrich_chats_with_dates_and_rank(chats: List[dict]) -> None:
    """Добавляет last_message_date_iso из date_tz (timestamptz) для отображения в браузере."""
    for chat in chats:
        val = chat.get("last_message_date")
        if val is None:
            chat["last_message_date_iso"] = None
        elif hasattr(val, "isoformat"):
            chat["last_message_date_iso"] = val.isoformat()
        else:
            from datetime import datetime, timezone
            try:
                dt = datetime.fromtimestamp(int(val), tz=timezone.utc)
                chat["last_message_date_iso"] = dt.isoformat()
            except (TypeError, ValueError, OSError):
                chat["last_message_date_iso"] = None


async def _enrich_chats_with_top_rank(db: AsyncSession, chats: List[dict]) -> None:
    """Добавляет top_subscriber_rank для абонентов из ТОП-50."""
    if not chats:
        return
    top_rows = await TopActiveSubscriberDAO.find_all(db)
    rank_map = {}
    for r in top_rows:
        uid, rank = r.get("uid"), r.get("rank")
        if uid is not None and rank is not None:
            try:
                rank_map[int(uid)] = int(rank)
            except (TypeError, ValueError):
                pass
    for chat in chats:
        chat["top_subscriber_rank"] = rank_map.get(chat["chat_id"])


async def find_or_create_chat(db: AsyncSession, user_id: int) -> Optional[dict]:
    """Находит или «создаёт» чат с абонентом по user_id. Чат идентифицируется по user_id;
    если сообщений ещё не было — возвращает данные для открытия пустого чата."""
    user = await get_user_short_info(db, user_id)
    if not user:
        return None
    r = await db.execute(
        text("""
            SELECT 1 FROM radius.radacct r
            JOIN users.user u ON lower(u.login) = lower(r.username)
            WHERE u.id = :uid AND r.acctstoptime IS NULL LIMIT 1
        """),
        {"uid": user_id}
    )
    is_online = 1 if r.scalar() else 0
    return {
        "chat_id": user_id,
        "fullname": user.get("fio") or f"Пользователь #{user_id}",
        "station_name": user.get("station_name") or "",
        "last_message_text": "",
        "last_message_date": 0,
        "last_message_date_iso": None,
        "is_online": is_online,
        "unread_count": 0,
        "has_unread": False,
        "is_jur": False,
        "top_subscriber_rank": None,
    }


async def search_users_chats(
    db: AsyncSession,
    query: str,
    limit: int
) -> List[dict]:
    """Поиск чатов по ID или ФИО."""
    is_id_search = query.isdigit()
    params = {"limit": limit}

    if is_id_search:
        sql_query = """
            WITH latest_messages AS (
                SELECT 
                    u.id as chat_id,
                    INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic) AS fullname, 
                    CASE 
                        WHEN sf.station_name IS NULL THEN ig.name 
                        ELSE sf.station_name 
                    END AS station_name,
                    MAX(um.date_tz) AS last_message_date,
                    (array_agg(um."text" ORDER BY um.date_tz DESC NULLS LAST))[1] AS last_message_text,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM radius.radacct r 
                            WHERE lower(r.username) = lower(u.login)
                                AND r.acctstoptime IS NULL
                        ) THEN 1 
                        ELSE 0 
                    END AS is_online
                FROM users.user_mail um
                LEFT JOIN users.user u 
                    ON u.id = um.id_user_from OR u.id = um.id_user_to
                LEFT JOIN wifitochka.ip_group ig 
                    ON ig.id = u.id_grp 
                LEFT JOIN users.user_details ud 
                    ON ud.user_id = u.id
                LEFT JOIN stations.station_forms sf 
                    ON sf.station_id = ig.id
                WHERE ud."name" IS NOT NULL AND u.id = :search_id
                GROUP BY u.id, ud.surname, ud.name, ud.patronymic, sf.station_name, ig.name, u.login
            )
            SELECT 
                chat_id,
                fullname,
                station_name,
                COALESCE(last_message_text, '') AS last_message_text,
                last_message_date,
                is_online
            FROM latest_messages
            ORDER BY last_message_date DESC NULLS LAST
            LIMIT :limit;
        """
        params["search_id"] = int(query)
    else:
        sql_query = """
            WITH latest_messages AS (
                SELECT 
                    u.id as chat_id,
                    INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic) AS fullname, 
                    CASE 
                        WHEN sf.station_name IS NULL THEN ig.name 
                        ELSE sf.station_name 
                    END AS station_name,
                    MAX(um.date_tz) AS last_message_date,
                    (array_agg(um."text" ORDER BY um.date_tz DESC NULLS LAST))[1] AS last_message_text,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM radius.radacct r 
                            WHERE lower(r.username) = lower(u.login)
                                AND r.acctstoptime IS NULL
                        ) THEN 1 
                        ELSE 0 
                    END AS is_online
                FROM users.user_mail um
                LEFT JOIN users.user u 
                    ON u.id = um.id_user_from OR u.id = um.id_user_to
                LEFT JOIN wifitochka.ip_group ig 
                    ON ig.id = u.id_grp 
                LEFT JOIN users.user_details ud 
                    ON ud.user_id = u.id
                LEFT JOIN stations.station_forms sf 
                    ON sf.station_id = ig.id
                WHERE ud."name" IS NOT NULL
                    AND (
                        LOWER(INITCAP(ud.surname) || ' ' || INITCAP(ud.name) || ' ' || INITCAP(ud.patronymic)) LIKE LOWER(:search_fullname)
                        OR LOWER(ud.surname) LIKE LOWER(:search_fullname)
                        OR LOWER(ud.name) LIKE LOWER(:search_fullname)
                        OR LOWER(ud.patronymic) LIKE LOWER(:search_fullname)
                    )
                GROUP BY u.id, ud.surname, ud.name, ud.patronymic, sf.station_name, ig.name, u.login
            )
            SELECT 
                chat_id,
                fullname,
                station_name,
                COALESCE(last_message_text, '') AS last_message_text,
                last_message_date,
                is_online
            FROM latest_messages
            ORDER BY last_message_date DESC NULLS LAST
            LIMIT :limit;
        """
        params["search_fullname"] = f"%{query}%"

    result = await db.execute(text(sql_query), params)
    rows = result.mappings().all()
    logger.info(f"Found {len(rows)} chats with query '{query}'")
    chats = [dict(row) for row in rows]
    _enrich_chats_with_dates_and_rank(chats)
    await _enrich_chats_with_top_rank(db, chats)
    return chats


def _row_to_message_dict(row: dict) -> dict:
    """Преобразование строки из БД в словарь сообщения с date_iso."""
    d = dict(row)
    date_val = d.pop("date_ts", None)
    if date_val is not None and hasattr(date_val, "isoformat"):
        d["date_iso"] = date_val.isoformat()
    elif date_val is not None and getattr(date_val, "__int__", None):
        from datetime import datetime, timezone
        try:
            d["date_iso"] = datetime.fromtimestamp(int(date_val), tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            d["date_iso"] = None
    else:
        d["date_iso"] = None
    d["date"] = d.get("date") or ""
    d["whose_message"] = d.get("whose_message") or "—"
    # subscriber_read_at: дата прочтения сообщения абонентом (person_type='user')
    sub_read = d.get("subscriber_read_at")
    if sub_read is not None and hasattr(sub_read, "isoformat"):
        d["subscriber_read_at"] = sub_read.isoformat()
    elif sub_read is not None and isinstance(sub_read, str):
        d["subscriber_read_at"] = sub_read
    else:
        d["subscriber_read_at"] = None
    # Нормализация has_read: явно считаем прочитанными легаси (read=1 при отсутствии user_mail_reads)
    v = d.get("has_read")
    from_table = d.get("read_from_table") is True or d.get("read_from_table") == 1
    legacy_read_one = str(d.get("legacy_read", "") or "").strip() == "1"
    if not from_table and legacy_read_one:
        d["has_read"] = True
    else:
        d["has_read"] = v is True or v == 1 or (isinstance(v, str) and v.lower() in ("true", "1", "t", "yes"))
    d.pop("legacy_read", None)
    rs = d.get("relay_snippet")
    if rs is not None:
        d["relay_snippet"] = _plain_text_reply_snippet(rs)
    rmid = d.get("relay_msg_id")
    if rmid is not None and str(rmid).strip():
        if d.get("relay_author") is None and not d.get("relay_snippet"):
            d["relay_deleted"] = True
    return d


async def get_users_messages(
    db: AsyncSession,
    chat_id: int,
    operator: dict,
    limit: int = 10,
    offset: int = 0,
    since_timestamp: Optional[int] = None,
    after_id: Optional[int] = None,
    before_id: Optional[int] = None,
    around_msg_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
) -> List[dict]:
    """Получение сообщений чата. ticket_id: только сообщения, закреплённые за тикетом."""
    user_id = operator.get('user_id')
    role = operator.get('role')

    if around_msg_id is not None:
        return await _get_messages_around(db, chat_id, operator, around_msg_id, user_id, role, ticket_id=ticket_id)

    where_clause = "WHERE (um.user_chat = :chat_id OR (um.user_chat IS NULL AND (um.id_user_from = :chat_id OR um.id_user_to = :chat_id)))"
    params = {
        "chat_id": chat_id,
        "user_id": user_id,
        "limit": limit,
        "offset": offset,
        "role": role,
        "relay_snippet_raw_max": _RELAY_SNIPPET_RAW_MAX,
    }
    if ticket_id is not None:
        where_clause += " AND um.ticket_id = :ticket_id"
        params["ticket_id"] = ticket_id

    if before_id is not None:
        where_clause += " AND um.id < :before_id"
        params["before_id"] = before_id
    if after_id is not None:
        where_clause += " AND um.id > :after_id"
        params["after_id"] = after_id
    elif since_timestamp is not None and before_id is None:
        where_clause += " AND um.date_tz > (to_timestamp(:since_timestamp) AT TIME ZONE 'UTC')"
        params["since_timestamp"] = since_timestamp

    order_limit = "ORDER BY um.id DESC LIMIT :limit OFFSET :offset"
    if before_id is not None:
        order_limit = "ORDER BY um.id DESC LIMIT :limit OFFSET 0"
    if after_id is not None:
        order_limit = "ORDER BY um.id ASC LIMIT :limit"

    query = text(f"""
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
                           WHEN um.person_type = 'skystream' THEN COALESCE(au_author.full_name, 'Инженер')
                           WHEN um.person_type = 'bot' THEN au_bot.full_name
                           WHEN um.person_type = 'partner' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'partner' THEN d_author.fullname
                           WHEN um.person_type = 'user' THEN 'Абонент'
                           WHEN um.person_type = 'tech' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'tech' THEN t_author.full_name
                           ELSE '—' END
                 ELSE CASE WHEN um.id_user_from = 2 THEN 'Контактный сервис' WHEN um.id_user_from = :chat_id THEN 'Пользователь'
                           WHEN um.id_user_from = :user_id THEN 'Вы'
                           WHEN au.full_name IS NOT NULL THEN au.full_name ELSE 'Неизвестный отправитель' END END AS whose_message,
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
                WHEN au2.full_name IS NOT NULL THEN au2.full_name ELSE 'Неизвестный' END AS relay_author
        FROM users.user_mail um
        LEFT JOIN users.skystream_users au ON au.id = um.id_user_from
        LEFT JOIN users.skystream_users au_author ON au_author.id = um.user_id AND um.person_type = 'skystream'
        LEFT JOIN users.skystream_users au_bot ON au_bot.id = um.user_id AND um.person_type = 'bot'
        LEFT JOIN partner.diler d_author ON d_author.id = um.user_id AND um.person_type = 'partner'
        LEFT JOIN partner.technicians t_author ON t_author.technician_id = um.user_id AND um.person_type = 'tech'
        LEFT JOIN users.user_mail um2 ON um2.id = NULLIF(trim(COALESCE(um.relay_msg_id, '')), '')::bigint
        LEFT JOIN users.skystream_users au2 ON au2.id = um2.id_user_from
        {where_clause}
        {order_limit}
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()
    logger.info(f"Retrieved {len(rows)} messages for chat {chat_id}, after_id={after_id}, before_id={before_id}")
    messages = [_row_to_message_dict(dict(row)) for row in rows]
    msg_ids = [m["msg_id"] for m in messages]
    attachments_map = await get_attachments_for_messages(db, msg_ids)
    for m in messages:
        m["attachments"] = attachments_map.get(m["msg_id"], [])
    return messages


async def get_messages_by_ids(
    db: AsyncSession,
    chat_id: int,
    operator: dict,
    msg_ids: List[int],
    ticket_id: Optional[int] = None,
) -> List[dict]:
    """Актуальное состояние сообщений по списку id (для поллинга правок/удалений)."""
    if not msg_ids:
        return []

    user_id = operator.get("user_id")
    role = operator.get("role")
    ids_placeholder = ", ".join(str(int(i)) for i in msg_ids)

    where_clause = (
        f"WHERE um.id IN ({ids_placeholder})"
        " AND (um.user_chat = :chat_id OR (um.user_chat IS NULL AND (um.id_user_from = :chat_id OR um.id_user_to = :chat_id)))"
    )
    params = {
        "chat_id": chat_id,
        "user_id": user_id,
        "role": role,
        "relay_snippet_raw_max": _RELAY_SNIPPET_RAW_MAX,
    }
    if ticket_id is not None:
        where_clause += (
            " AND (um.ticket_id = :ticket_id OR EXISTS ("
            "SELECT 1 FROM users.tracker_ticket_mail_links l"
            " WHERE l.ticket_id = :ticket_id AND l.user_mail_id = um.id))"
        )
        params["ticket_id"] = ticket_id

    query = text(f"""
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
                           WHEN um.person_type = 'skystream' THEN COALESCE(au_author.full_name, 'Инженер')
                           WHEN um.person_type = 'bot' THEN au_bot.full_name
                           WHEN um.person_type = 'partner' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'partner' THEN d_author.fullname
                           WHEN um.person_type = 'user' THEN 'Абонент'
                           WHEN um.person_type = 'tech' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'tech' THEN t_author.full_name
                           ELSE '—' END
                 ELSE CASE WHEN um.id_user_from = 2 THEN 'Контактный сервис' WHEN um.id_user_from = :chat_id THEN 'Пользователь'
                           WHEN um.id_user_from = :user_id THEN 'Вы'
                           WHEN au.full_name IS NOT NULL THEN au.full_name ELSE 'Неизвестный отправитель' END END AS whose_message,
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
                WHEN au2.full_name IS NOT NULL THEN au2.full_name ELSE 'Неизвестный' END AS relay_author
        FROM users.user_mail um
        LEFT JOIN users.skystream_users au ON au.id = um.id_user_from
        LEFT JOIN users.skystream_users au_author ON au_author.id = um.user_id AND um.person_type = 'skystream'
        LEFT JOIN users.skystream_users au_bot ON au_bot.id = um.user_id AND um.person_type = 'bot'
        LEFT JOIN partner.diler d_author ON d_author.id = um.user_id AND um.person_type = 'partner'
        LEFT JOIN partner.technicians t_author ON t_author.technician_id = um.user_id AND um.person_type = 'tech'
        LEFT JOIN users.user_mail um2 ON um2.id = NULLIF(trim(COALESCE(um.relay_msg_id, '')), '')::bigint
        LEFT JOIN users.skystream_users au2 ON au2.id = um2.id_user_from
        {where_clause}
        ORDER BY um.id ASC
    """)

    result = await db.execute(query, params)
    messages = [_row_to_message_dict(dict(row)) for row in result.mappings().all()]
    found_ids = [m["msg_id"] for m in messages]
    attachments_map = await get_attachments_for_messages(db, found_ids)
    own_support_ids = [
        m["msg_id"] for m in messages
        if int(m.get("user_id") or 0) == int(user_id or 0) and int(m.get("answer") or 0) == 1
    ] if user_id else []
    reads_map = await get_messages_reads_batch(db, own_support_ids) if own_support_ids else {}
    for m in messages:
        m["attachments"] = attachments_map.get(m["msg_id"], [])
        if m["msg_id"] in reads_map:
            m["reads"] = reads_map[m["msg_id"]]
    return messages


async def get_message_preview(
    db: AsyncSession,
    chat_id: int,
    msg_id: int,
    operator: dict,
) -> Optional[dict]:
    """Получить одно сообщение по id для превью (текст, вложения, ticket_id). Сообщение должно относиться к чату chat_id."""
    user_id = operator.get("user_id")
    role = operator.get("role")
    query = text("""
        SELECT
            um.id AS msg_id,
            um.date_tz AS date_ts,
            um."text",
            CASE WHEN um.file_new IS NULL OR um.file_new = '0' OR um.file_new = '' THEN NULL ELSE um.file_new END AS file_path,
            CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                 THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END ELSE um.answer END AS answer,
            CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                 THEN CASE WHEN um.person_type = 'skystream' AND um.user_id = :user_id THEN 'Вы'
                           WHEN um.person_type = 'skystream' THEN COALESCE(au_author.full_name, 'Инженер')
                           WHEN um.person_type = 'bot' THEN au_bot.full_name
                           WHEN um.person_type = 'partner' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'partner' THEN d_author.fullname
                           WHEN um.person_type = 'user' THEN 'Абонент'
                           WHEN um.person_type = 'tech' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'tech' THEN t_author.full_name ELSE '—' END
                 ELSE CASE WHEN um.id_user_from = 2 THEN 'Контактный сервис' WHEN um.id_user_from = :chat_id THEN 'Пользователь'
                           WHEN um.id_user_from = :user_id THEN 'Вы'
                           WHEN au.full_name IS NOT NULL THEN au.full_name ELSE 'Неизвестный отправитель' END END AS whose_message,
            um.ticket_id,
            um.user_chat,
            um.id_user_from,
            um.id_user_to,
            um.relay_msg_id,
            LEFT(um2."text", :relay_snippet_raw_max) AS relay_snippet,
            CASE WHEN um2.id IS NULL THEN NULL WHEN um2.id_user_from = 2 THEN 'Контактный сервис'
                WHEN um2.id_user_from = :chat_id THEN 'Пользователь' WHEN um2.id_user_from = :user_id THEN 'Вы'
                WHEN au2.full_name IS NOT NULL THEN au2.full_name ELSE 'Неизвестный' END AS relay_author
        FROM users.user_mail um
        LEFT JOIN users.skystream_users au ON au.id = um.id_user_from
        LEFT JOIN users.skystream_users au_author ON au_author.id = um.user_id AND um.person_type = 'skystream'
        LEFT JOIN users.skystream_users au_bot ON au_bot.id = um.user_id AND um.person_type = 'bot'
        LEFT JOIN partner.diler d_author ON d_author.id = um.user_id AND um.person_type = 'partner'
        LEFT JOIN partner.technicians t_author ON t_author.technician_id = um.user_id AND um.person_type = 'tech'
        LEFT JOIN users.user_mail um2 ON um2.id = NULLIF(trim(COALESCE(um.relay_msg_id, '')), '')::bigint
        LEFT JOIN users.skystream_users au2 ON au2.id = um2.id_user_from
        WHERE um.id = :msg_id
    """)
    result = await db.execute(
        query,
        {
            "msg_id": msg_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "role": role,
            "relay_snippet_raw_max": _RELAY_SNIPPET_RAW_MAX,
        },
    )
    row = result.mappings().first()
    if not row:
        return None
    row_d = dict(row)
    # Проверка принадлежности чату в Python (старые данные — типы/нули)
    try:
        cid = int(chat_id)
        uc = row_d.get("user_chat")
        uf = int(row_d.get("id_user_from") or 0)
        ut = int(row_d.get("id_user_to") or 0)
        belongs = uc == cid or uf == cid or ut == cid
        legacy_unknown = uc is None and uf == 0 and ut == 0  # старая запись без участников
        if not (belongs or legacy_unknown):
            return None
    except (TypeError, ValueError):
        return None
    for k in ("user_chat", "id_user_from", "id_user_to"):
        row_d.pop(k, None)
    msg = _row_to_message_dict(row_d)
    attachments_map = await get_attachments_for_messages(db, [msg_id])
    msg["attachments"] = attachments_map.get(msg_id, [])
    return msg


async def _get_messages_around(
    db: AsyncSession,
    chat_id: int,
    operator: dict,
    around_msg_id: int,
    user_id: int,
    role: str,
    ticket_id: Optional[int] = None,
) -> List[dict]:
    """Порция из 11 сообщений: 5 выше + центр + 5 ниже по id."""
    base = """
        SELECT um.id AS msg_id, um.date_tz AS date_ts, um."text",
            CASE WHEN um.file_new IS NULL OR um.file_new = '0' OR um.file_new = '' THEN NULL ELSE um.file_new END AS file_path,
            CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                 THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END ELSE um.answer END AS answer,
            CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                 THEN CASE WHEN um.person_type = 'skystream' AND um.user_id = :user_id THEN 'Вы'
                           WHEN um.person_type = 'skystream' THEN COALESCE(au_author.full_name, 'Инженер')
                           WHEN um.person_type = 'bot' THEN au_bot.full_name
                           WHEN um.person_type = 'partner' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'partner' THEN d_author.fullname
                           WHEN um.person_type = 'user' THEN 'Абонент'
                           WHEN um.person_type = 'tech' AND :role = 'support' THEN 'ПАРТНЕР'
                           WHEN um.person_type = 'tech' THEN t_author.full_name ELSE '—' END
                 ELSE CASE WHEN um.id_user_from = 2 THEN 'Контактный сервис' WHEN um.id_user_from = :chat_id THEN 'Пользователь'
                           WHEN um.id_user_from = :user_id THEN 'Вы'
                           WHEN au.full_name IS NOT NULL THEN au.full_name ELSE 'Неизвестный отправитель' END END AS whose_message,
            ((EXISTS (SELECT 1 FROM users.user_mail_reads r WHERE r.msg_id = um.id AND r.user_id <> COALESCE(um.user_id, um.id_user_from)))
             OR ((NOT (EXISTS (SELECT 1 FROM users.user_mail_reads r2 WHERE r2.msg_id = um.id))) AND (TRIM(COALESCE(um."read"::text, '0')) = '1'))
             OR (um.date_tz < '2026-01-01'::timestamptz)) AS has_read,
            (EXISTS (SELECT 1 FROM users.user_mail_reads r WHERE r.msg_id = um.id)) AS read_from_table,
            (SELECT r.read_time FROM users.user_mail_reads r WHERE r.msg_id = um.id AND r.person_type = 'user' ORDER BY r.read_time ASC LIMIT 1) AS subscriber_read_at,
            TRIM(COALESCE(um."read"::text, '0')) AS legacy_read,
            COALESCE(um.user_id, um.id_user_from) AS user_id,
            um.relay_msg_id, LEFT(um2."text", :relay_snippet_raw_max) AS relay_snippet,
            CASE WHEN um2.id IS NULL THEN NULL WHEN um2.id_user_from = 2 THEN 'Контактный сервис'
                WHEN um2.id_user_from = :chat_id THEN 'Пользователь' WHEN um2.id_user_from = :user_id THEN 'Вы'
                WHEN au2.full_name IS NOT NULL THEN au2.full_name ELSE 'Неизвестный' END AS relay_author
        FROM users.user_mail um
        LEFT JOIN users.skystream_users au ON au.id = um.id_user_from
        LEFT JOIN users.skystream_users au_author ON au_author.id = um.user_id AND um.person_type = 'skystream'
        LEFT JOIN users.skystream_users au_bot ON au_bot.id = um.user_id AND um.person_type = 'bot'
        LEFT JOIN partner.diler d_author ON d_author.id = um.user_id AND um.person_type = 'partner'
        LEFT JOIN partner.technicians t_author ON t_author.technician_id = um.user_id AND um.person_type = 'tech'
        LEFT JOIN users.user_mail um2 ON um2.id = NULLIF(trim(COALESCE(um.relay_msg_id, '')), '')::bigint
        LEFT JOIN users.skystream_users au2 ON au2.id = um2.id_user_from
        WHERE (um.user_chat = :chat_id OR (um.user_chat IS NULL AND (um.id_user_from = :chat_id OR um.id_user_to = :chat_id)))
    """
    if ticket_id is not None:
        base += " AND um.ticket_id = :ticket_id"
    params = {
        "chat_id": chat_id,
        "user_id": user_id,
        "role": role,
        "around_msg_id": around_msg_id,
        "relay_snippet_raw_max": _RELAY_SNIPPET_RAW_MAX,
    }
    if ticket_id is not None:
        params["ticket_id"] = ticket_id
    # 6 сообщений: центр + 5 выше (id <= around, order desc limit 6)
    q_before = text(base + " AND um.id <= :around_msg_id ORDER BY um.id DESC LIMIT 6")
    # 5 сообщений ниже (id > around, order asc limit 5)
    q_after = text(base + " AND um.id > :around_msg_id ORDER BY um.id ASC LIMIT 5")
    r1 = await db.execute(q_before, params)
    rows_before = list(r1.mappings().all())
    r2 = await db.execute(q_after, params)
    rows_after = list(r2.mappings().all())
    before_list = list(reversed(rows_before))
    after_list = rows_after
    combined = before_list + after_list
    messages = [_row_to_message_dict(dict(row)) for row in combined]
    msg_ids = [m["msg_id"] for m in messages]
    attachments_map = await get_attachments_for_messages(db, msg_ids)
    for m in messages:
        m["attachments"] = attachments_map.get(m["msg_id"], [])
    return messages


async def mark_as_read(
    db: AsyncSession,
    message_ids: List[int],
    reader_user_id: int,
    person_type: str = "skystream",
) -> dict:
    """Отметить сообщения как прочитанные: всегда запись в user_mail_reads.
    read='1' в user_mail выставляется только если читающий — получатель сообщения (id_user_to = reader_user_id).
    Другой инженер при просмотре чата только добавляет запись в таблицу прочтений, не меняя read в user_mail."""
    if not message_ids:
        return {"status": "ok", "marked": 0}
    # Legacy: read='1' и new=0 только для сообщений, где читающий = получатель (абонент из ЛК прочитал)
    await db.execute(
        text("""
            UPDATE users.user_mail SET new = 0, read = '1'
            WHERE id = ANY(:ids) AND id_user_to = :reader_user_id
        """),
        {"ids": message_ids, "reader_user_id": reader_user_id}
    )
    # Оператор техподдержки прочитал входящие сообщения абонента (id_user_from > 1020):
    # снимаем флаг "new", чтобы чат перестал считаться непрочитанным и в счётчике навигации,
    # и в счётчике непрочитанных самого списка чатов.
    await db.execute(
        text("""
            UPDATE users.user_mail SET new = 0
            WHERE id = ANY(:ids) AND id_user_from > 1020
        """),
        {"ids": message_ids}
    )
    for msg_id in message_ids:
        await db.execute(
            text("""
                INSERT INTO users.user_mail_reads (msg_id, user_id, person_type)
                VALUES (:msg_id, :user_id, :person_type)
                ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
            """),
            {"msg_id": msg_id, "user_id": reader_user_id, "person_type": person_type}
        )
    await db.commit()
    return {"status": "ok", "marked": len(message_ids)}


async def get_message_reads(
    db: AsyncSession,
    msg_id: int,
) -> List[dict]:
    """Кто прочитал сообщение: список { display_name, read_time }.
    person_type: skystream -> skystream_users.full_name, partner -> diler.fullname,
    user -> user.full_name, tech -> technicians.full_name.
    """
    query = text("""
        SELECT r.read_time,
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
        WHERE r.msg_id = :msg_id
        ORDER BY r.read_time ASC
    """)
    result = await db.execute(query, {"msg_id": msg_id})
    rows = result.mappings().all()
    return [
        {
            "display_name": (r.get("display_name") or "—").strip() or "—",
            "read_time": r["read_time"].isoformat() if r.get("read_time") and hasattr(r["read_time"], "isoformat") else str(r.get("read_time") or ""),
        }
        for r in rows
    ]


async def get_messages_reads_batch(
    db: AsyncSession,
    msg_ids: List[int],
) -> dict:
    """Пакетное получение прочтений для списка сообщений user_mail."""
    if not msg_ids:
        return {}
    ids_placeholder = ", ".join(str(int(i)) for i in msg_ids)
    query = text(f"""
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
        WHERE r.msg_id IN ({ids_placeholder})
        ORDER BY r.read_time ASC
    """)
    result = await db.execute(query)
    out: dict = {mid: [] for mid in msg_ids}
    for r in result.mappings().all():
        mid = r["msg_id"]
        out.setdefault(mid, []).append({
            "display_name": (r.get("display_name") or "—").strip() or "—",
            "read_time": r["read_time"].isoformat() if r.get("read_time") and hasattr(r["read_time"], "isoformat") else str(r.get("read_time") or ""),
            "person_type": r.get("person_type"),
            "user_id": r.get("user_id"),
        })
    return out


async def get_number_unread_chats(
    db: AsyncSession,
    role: str
) -> dict:
    """Получить количество непрочитанных чатов и открытых трекеров."""
    line = 1 if role == 'support' else 2
    query = text("""
        SELECT
            (SELECT COUNT(DISTINCT CASE
                WHEN id_user_from > 1020 THEN id_user_from
                ELSE id_user_to
            END)
            FROM users.user_mail
            WHERE "new" = 1
            ) AS opened_chats,

            (SELECT COUNT(1)
            FROM users.tracker_tickets
            WHERE support_line = :line
                AND status IN ('pending', 'in_progress')
            ) AS opened_trackers;
    """)
    result = await db.execute(query, {'line': line})
    row = result.mappings().first()
    return dict(row) if row else {"opened_chats": 0, "opened_trackers": 0}