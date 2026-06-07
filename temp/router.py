from app.api.v1.routers.helpdesk.tickets import (
    INCIDENT_STATUS_TO_DB,
    _INCIDENT_STATUS_MAP,
    _INCIDENT_STATUS_DISPLAY,
    _INCIDENT_OPEN_STATUSES,
)
from datetime import datetime, timedelta, timezone
import json
import math
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, HTTPException, Response
import logging
from app.database import get_db, get_db_zabbix_optional, redis_client
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import MEDIA_DIR
from app.models.users import DBCategory, TrackerTicketMailLinks, TrackerMessageAttachment
from app.web.dependencies import allow_admin, allow_engineer, allow_manager, allow_support, allow_support_marketing, get_current_user, require_ticket_create
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, text
from app.api.v1.routers.helpdesk.dao import DBArticleDAO, DBCategoryDAO, DBNodeDAO, HelpdeskMacroDAO, TrackerMessagesDAO, TrackerTicketLineHistoryDAO, TrackerTicketMailLinksDAO, TrackerTicketsDAO, UserMailDAO
from app.api.v1.routers.helpdesk.schema import AddTicketExecutorSchema, AddTicketTechnicianSchema, ArticleDetailDTO, ArticleListResponse, AssignmentTarget, AssignmentUpdateSchema, BulkTicketsDeleteSchema, BulkTicketsUpdateSchema, CategoryDTO, ChatMessageDTO, DistributeTicketsSchema, HomeResponse, InternalCommentCreate, KBNodeDTO, MessageUpdate, StatusUpdateSchema, TicketCreateSchema, TicketStatusAction
from app.api.v1.routers.helpdesk.tickets import assign_new_line_history, bulk_delete_tickets, bulk_update_tickets, client_replied_sla_update, close_ticket_line_history, distribute_tickets_roundrobin, ensure_engineer_participant_on_message, get_ticket_history_data, get_tickets, get_helpdesk_nav_tickets_count, get_helpdesk_nav_unread_tickets_count, get_helpdesk_sidebar_counts, get_helpdesk_partner_unread_count, get_tracker_views_counts, get_user_messages_for_ticket, operator_replied_sla_update, reopen_ticket_line_history
from app.api.v1.routers.helpdesk.user_short_info_in_chat import formate_user_chat_info
from app.api.v1.routers.helpdesk.chat_files import (
    disk_path_from_media_url,
    persist_chat_file_bytes,
    read_upload_file,
    resolve_tracker_storage_scope,
)
from app.api.v1.routers.helpdesk.tracker_attachments import (
    collect_upload_files_from_form,
    persist_tracker_attachments_background,
    prepare_tracker_upload_files,
    resolve_tracker_attachment_download,
    save_tracker_message_attachments,
    save_tracker_prepared_attachments,
    tracker_attachment_file_response,
)
from app.api.v1.routers.helpdesk.chat_upload_tokens import (
    cleanup_temp_files,
    load_upload_tokens,
    save_attachment_temp,
)
from app.api.v1.routers.helpdesk.users_chats import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    _check_file_magic,
    create_response,
    delete_chat_attachment,
    find_or_create_chat,
    get_all_users_chats,
    get_message_preview,
    get_message_reads,
    get_messages_by_ids,
    get_messages_reads_batch,
    get_number_unread_chats,
    get_users_messages,
    mark_as_read,
    process_form_data,
    resolve_mail_attachment_download,
    save_chat_attachment,
    save_mail_prepared_attachments,
    save_message_to_db,
    search_users_chats,
)
from app.schemas.chat import Chat, Message, MessageCreate
from app.utils.auxiliary_functions import get_client_ip
from app.constants import STATUS_DISPLAY, TRACKER_CLOSED_STATUSES, TRACKER_OPEN_STATUSES
from app.api.v1.routers.stations.dao import AlivenessStatusDAO, IpGroupDAO, StationFormsDAO, VirtualNetworkOperatorDAO
from app.api.v1.routers.stations.station_profile import get_last_hour_metrics, get_users_short_info
from app.api.v1.routers.stations.funcs import get_yesterday_ym
from app.api.v1.routers.stations.station_profile import define_signal_and_bytegz_status
from app.api.v1.routers.statistics.dao import MonthlyStationStatsDAO, SatelliteThresholdsDAO

logger = logging.getLogger("abs")


def _parse_optional_reply_to_id(value: Any) -> Optional[int]:
    """ID сообщения для reply_to_id (из JSON/формы может прийти строкой)."""
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            parsed = int(value)
            return parsed if parsed > 0 else None
        except ValueError:
            return None
    return None


router = APIRouter(
    prefix="/helpdesk",
    tags=["Chat & Tracker"]
)

#######################
### Чат с абонентом ###
#######################

# ───────────────────────────────────────────────
# GET /database/full — база знаний
# ───────────────────────────────────────────────


@router.get("/database/full")
async def get_kb_full():
    """Возвращает ВСЕ статьи сразу — для мгновенного поиска на фронте"""
    # Если данные статичны — можно оставить как есть.
    # Если будут из БД — вынеси в сервис с db.
    return {
        "articles": [
            {
                "id": 1,
                "title": "Низкая скорость интернета",
                "answers": [
                    {"page_title": "Проверка по Wi-Fi или кабелю",
                        "text": "Уточните, пожалуйста, измеряете скорость по Wi-Fi или по кабелю?"},
                    {"page_title": "Рекомендация",
                        "text": "Если по Wi-Fi — подключитесь по кабелю и проверьте снова."}
                ]
            },
            # ... остальные статьи
        ]
    }


# ───────────────────────────────────────────────
# GET /chats/all — все чаты
# ───────────────────────────────────────────────
@router.get("/chats/all", response_model=List[Chat])
async def get_chats(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_users_chats(db, limit=limit, offset=offset)

# ───────────────────────────────────────────────
# GET /chats/updates — поллинг новых чатов
# ───────────────────────────────────────────────


@router.get("/chats/updates", response_model=List[Chat])
async def get_chat_updates(
    last_sync: float = Query(0),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    # Если пришел 0 или NaN (защита на стороне сервера)
    if not last_sync or math.isnan(last_sync):
        # Если клиент прислал 0, возвращаем пустой список, чтобы не вешать базу
        return []

    # Приводим к целому числу (секунды)
    return await get_all_users_chats(db, since_timestamp=int(last_sync))

# ───────────────────────────────────────────────
# GET /chats/unread_chats — непрочитанные
# ───────────────────────────────────────────────


@router.get("/chats/unread_chats")
async def get_chats_unread(
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список непрочитанных чатов"""
    user_id = user.get('user_id')
    role = user.get('role')

    # 1. Формируем ключ кэша
    cache_key = f"unread_stats:{user_id}"

    # 2. Пробуем достать из Redis
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # 3. Если нет в кэше — идем в БД
    result = await get_number_unread_chats(db, role)

    # 4. Сохраняем в Redis на 5 секунд (TTL)
    # Это снизит нагрузку на БД в разы и позволит "сгладить" поллинг
    await redis_client.setex(cache_key, 10, json.dumps(result))

    return result


# ───────────────────────────────────────────────
# GET /macros — список макросов для тикета (сообщение + опционально статус/приоритет)
# ───────────────────────────────────────────────
@router.get("/macros")
async def list_macros(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список макросов для выпадающего списка на странице тикета."""
    items = await HelpdeskMacroDAO.list_for_ticket(db)
    return {"macros": items}


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/userinfo — инфо о пользователе
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/userinfo")
async def user_info(
    chat_id: int,
    ticket_id: Optional[int] = Query(
        None, description="Исключить тикет из блока прошлых тикетов"),
    brief: bool = Query(
        False, description="Только ФИО/организация, станция и ID (без тарифа и финансов)"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Краткая информация об абоненте (для сайдбара тикета и чата)."""
    return await formate_user_chat_info(
        db, chat_id, exclude_ticket_id=ticket_id, brief=brief)

# ───────────────────────────────────────────────
# GET /users/{user_id}/tickets — тикеты абонента с фильтрами и пагинацией
# ───────────────────────────────────────────────


@router.get("/users/{user_id}/tickets")
async def get_user_tickets(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    category_id: Optional[int] = Query(None),
    executor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Получить все тикеты пользователя с фильтрацией и пагинацией.
    Для role=support в блоке «История тикетов» возвращаются только тикеты с source in ('lk', 'ks')."""
    filters = {"user_id": user_id}
    if category_id is not None:
        filters["category_id"] = category_id
    if executor_id is not None:
        filters["assigned_to"] = executor_id
    if operator.get("role") == "support":
        filters["source_in"] = ["lk", "ks"]
    # Сортировка для блока «История тикетов»: открытые → я исполнитель → остальные открытые → закрытые; внутри группы по приоритету
    current_user_id = operator.get("user_id")
    if current_user_id is not None:
        filters["sort_sidebar"] = True
        filters["current_user_id"] = int(current_user_id)

    result = await get_tickets(
        db=db,
        user_role=operator.get("role", "support"),
        all_statuses=True,
        page=page,
        per_page=per_page,
        filters=filters,
    )

    tickets = result.get("items", [])
    total = result.get("total", 0)
    total_pages = (total + per_page - 1) // per_page

    # Обогащаем информацию о тикетах
    enriched_tickets = []
    for ticket in tickets:
        # Определяем slug категории по названию для единообразного выделения цветом
        category_name = ticket.get("category", "")
        category_slug_map = {
            'Финансы': 'finance',
            'Работа сети': 'network',
            'Работа ЛК': 'lk',
            'Работа оборудования': 'equipment',
            'Прочее': 'other'
        }
        category_slug = category_slug_map.get(
            category_name, 'other') if category_name and category_name != '—' else 'other'

        enriched_ticket = {
            "id": ticket.get("id"),
            "title": ticket.get("title"),
            "category": ticket.get("category"),
            "category_id": ticket.get("category_id"),
            "category_slug": category_slug,
            "created_at": ticket.get("created_at"),
            "closed_at": ticket.get("closed_at"),
            "status": ticket.get("status"),
            "status_raw": ticket.get("status_raw"),
            "assigned_to": ticket.get("assigned_to_name"),
            "priority": ticket.get("priority"),
            "source_display": ticket.get("source_display"),
        }
        enriched_tickets.append(enriched_ticket)

    return {
        "items": enriched_tickets,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }

# ───────────────────────────────────────────────
# GET /users/{user_id}/tickets/filters — фильтры для тикетов (категории, исполнители)
# ───────────────────────────────────────────────


@router.get("/users/{user_id}/tickets/filters")
async def get_user_tickets_filters(
    user_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Получить доступные фильтры (категории, исполнители) для тикетов пользователя"""
    from app.models.users import TrackerTickets, User

    # Получаем все категории
    categories_query = select(DBCategory).order_by(DBCategory.name)
    categories_result = await db.execute(categories_query)
    categories = []
    for cat in categories_result.scalars().all():
        categories.append({
            "id": cat.id,
            "name": cat.name or "Без категории",
        })

    # Получаем исполнителей, которые работают над тикетами этого пользователя
    executors_query = (
        select(User.id, User.full_name)
        .join(TrackerTickets, TrackerTickets.engineer_id == User.id)
        .where(TrackerTickets.user_id == user_id)
        .distinct()
        .order_by(User.full_name)
    )
    executors_result = await db.execute(executors_query)
    executors = [
        {"id": row[0], "name": row[1]} for row in executors_result.fetchall()
    ]

    return {
        "categories": categories,
        "executors": executors,
    }

# ───────────────────────────────────────────────
# GET /chats/search — поиск чатов
# ───────────────────────────────────────────────


@router.get("/chats/search", response_model=List[Chat])
async def search_chats(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Поиск нужного чата"""
    return await search_users_chats(db, query, limit)


# ───────────────────────────────────────────────
# GET /chats/find-or-create — получить/открыть чат по user_id (даже без сообщений)
# ───────────────────────────────────────────────
@router.get("/chats/find-or-create")
async def find_or_create_chat_endpoint(
    user_id: int = Query(..., description="ID абонента"),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Возвращает данные чата с абонентом. Если диалога ещё не было — всё равно возвращает чат (пустой)."""
    chat = await find_or_create_chat(db, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return chat


# ───────────────────────────────────────────────
# POST /chats/{chat_id}/messages — новое сообщение
# ───────────────────────────────────────────────
@router.post("/chats/{chat_id}/messages")
async def create_message(
    request: Request,
    chat_id: int,
    background_tasks: BackgroundTasks,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Сохранить новое сообщение из чата.

    Принимает опциональное поле new_status из формы.
    Если ticket_id передан — паузирует SLA и обновляет line_history (state=waiting_client).
    Если new_status передан — меняет статус тикета через operator_replied_sla_update.
    """
    client_ip = get_client_ip(request)
    ts = int(datetime.now(timezone.utc).timestamp())
    formatted_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    current_op_id = operator.get('user_id')

    form = await request.form()
    text, file = await process_form_data(form)
    relay_msg_id = form.get("relay_msg_id") or None
    if relay_msg_id is not None and isinstance(relay_msg_id, str):
        relay_msg_id = relay_msg_id.strip() or None
    relay_author = (form.get("relay_author") or "").strip() or None
    relay_snippet = (form.get("relay_snippet") or "").strip() or None
    ticket_id = form.get("ticket_id")
    if ticket_id is not None:
        try:
            ticket_id = int(ticket_id)
        except (TypeError, ValueError):
            ticket_id = None

    new_status = (form.get("new_status") or "").strip() or None
    _allowed_statuses = ("in_progress", "waiting_client",
                         "resolved", "not_resolved", "cancelled", "deferred")
    if new_status not in _allowed_statuses:
        new_status = None

    raw_tokens = form.get("upload_tokens")
    upload_tokens: List[str] = []
    if raw_tokens:
        try:
            parsed = json.loads(raw_tokens) if isinstance(raw_tokens, str) else raw_tokens
            if isinstance(parsed, list):
                upload_tokens = [str(t) for t in parsed if t]
        except (ValueError, TypeError):
            upload_tokens = []

    token_attachments: List[dict] = []
    file_path = None

    # ── Двухфазный путь: сообщение + вложения в одной транзакции ──────────────
    if upload_tokens:
        prepared, tmp_paths = load_upload_tokens(upload_tokens, operator_id=current_op_id or 0)
        try:
            msg_id = await save_message_to_db(
                db, chat_id, current_op_id, text, "", None, client_ip,
                relay_msg_id=relay_msg_id, ticket_id=ticket_id, auto_commit=False,
            )
            actual_id = msg_id.get("id") if isinstance(msg_id, dict) else msg_id
            token_attachments = await save_mail_prepared_attachments(
                db, msg_id=actual_id, chat_id=chat_id, prepared=prepared,
                ticket_id=ticket_id, timestamp=ts, commit=False,
            )
            await db.commit()
        except HTTPException:
            raise
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Не удалось сохранить вложения")
        cleanup_temp_files(tmp_paths)
        if token_attachments:
            file_path = token_attachments[0].get("file_path")
    else:
        msg_id = await save_message_to_db(
            db, chat_id, current_op_id, text, "", None, client_ip,
            relay_msg_id=relay_msg_id, ticket_id=ticket_id,
        )
        actual_id = msg_id.get("id") if isinstance(msg_id, dict) else msg_id
        if file and file.filename:
            att = await save_chat_attachment(
                db, actual_id, chat_id, file, ticket_id=ticket_id, timestamp=ts,
            )
            file_path = att.get("file_path")

    # Если отправлено в рамках тикета — обновляем SLA + line_history в фоне
    if ticket_id:
        background_tasks.add_task(
            operator_replied_sla_update,
            ticket_id=ticket_id,
            user_id=current_op_id,
            new_status=new_status,
        )
        # Инженер (не support): если не в тикете — назначить основным или добавить в исполнители
        op_role = (operator.get("role") or "").lower()
        participant_update = await ensure_engineer_participant_on_message(db, ticket_id, current_op_id, op_role)
    else:
        participant_update = None

    out = create_response(
        actual_id, text, file_path, formatted_time, current_op_id,
        relay_msg_id=relay_msg_id, relay_author=relay_author, relay_snippet=relay_snippet,
    )
    if token_attachments:
        out["attachments"] = token_attachments
    if participant_update:
        out.update(participant_update)
    return out


# ───────────────────────────────────────────────
# POST /chats/{chat_id}/attachments/upload — фаза A двухфазной отправки
# ───────────────────────────────────────────────
@router.post("/chats/{chat_id}/attachments/upload")
async def upload_chat_attachment_token(
    chat_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить ОДИН файл во временную папку ДО создания сообщения.
    Возвращает подписанный токен (запись в БД не делается)."""
    form = await request.form()
    file = form.get("file")
    if not file or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="Файл не передан")
    contents, original_filename = await read_upload_file(file)
    return save_attachment_temp(contents, original_filename, operator_id=operator.get("user_id") or 0)


# ───────────────────────────────────────────────
# POST /chats/{chat_id}/messages/{msg_id}/attachments — прикрепить файл к сообщению
# ───────────────────────────────────────────────
@router.post("/chats/{chat_id}/messages/{msg_id}/attachments")
async def add_message_attachment(
    chat_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить один файл-вложение к сообщению. Лимит 15 МБ. По одному файлу за запрос."""
    form = await request.form()
    file = form.get("file")
    if not file or not hasattr(file, "filename"):
        raise HTTPException(status_code=400, detail="Файл не передан")
    from app.models.users import UserMail
    check = await db.execute(
        select(UserMail.id).where(
            UserMail.id == msg_id,
            or_(
                UserMail.user_chat == chat_id,
                (UserMail.user_chat.is_(None)) & (
                    (UserMail.id_user_from == chat_id) | (
                        UserMail.id_user_to == chat_id)
                ),
            ),
        ).limit(1)
    )
    if not check.scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail="Сообщение не найдено в этом чате")
    ticket_id = form.get("ticket_id")
    if ticket_id is not None:
        try:
            ticket_id = int(ticket_id)
        except (TypeError, ValueError):
            ticket_id = None
    attachment = await save_chat_attachment(
        db, msg_id, chat_id, file, ticket_id=ticket_id,
    )
    return attachment


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages — история чата
# ───────────────────────────────────────────────


@router.get("/chats/{chat_id}/messages", response_model=List[Message])
async def get_messages(
    chat_id: int,
    operator: Dict = Depends(allow_support),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    around_msg_id: Optional[int] = Query(
        None, description="Порция 11 сообщений вокруг этого id"),
    before_id: Optional[int] = Query(
        None, description="Сообщения с id < before_id (подгрузка вверх)"),
    after_id: Optional[int] = Query(
        None, description="Сообщения с id > after_id (подгрузка вниз)"),
    ticket_id: Optional[int] = Query(
        None, description="ID тикета: только сообщения этого тикета"),
    db: AsyncSession = Depends(get_db),
):
    """Сообщения конкретного чата"""
    return await get_users_messages(
        db, chat_id, operator, limit=limit, offset=offset,
        around_msg_id=around_msg_id, before_id=before_id, after_id=after_id,
        ticket_id=ticket_id,
    )

# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/updates — новые сообщения
# ───────────────────────────────────────────────


@router.get("/chats/{chat_id}/messages/updates", response_model=List[Message])
async def get_new_messages(
    chat_id: int,
    after_id: Optional[int] = Query(
        None, description="Возвращать только сообщения с id > after_id"),
    since: Optional[str] = None,
    ticket_id: Optional[int] = Query(
        None, description="ID тикета: только сообщения этого тикета"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Поллинг новых сообщений. Предпочтительно передавать after_id (id последнего известного сообщения)."""
    since_timestamp = None
    if since and after_id is None:
        try:
            if 'T' in since:
                dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                since_timestamp = int(dt.timestamp())
            else:
                dt = datetime.strptime(since, "%d.%m.%Y %H:%M")
                since_timestamp = int(dt.replace(
                    tzinfo=pytz.timezone("Europe/Moscow")).timestamp())
        except Exception as e:
            logger.warning("Error parsing 'since' date: %s", e)
            raise HTTPException(
                status_code=400, detail="Invalid 'since' format")

    result = await get_users_messages(
        db, chat_id=chat_id, operator=operator, limit=50, offset=0,
        since_timestamp=since_timestamp, after_id=after_id,
        ticket_id=ticket_id,
    )
    return result


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/sync — синхронизация правок/удалений
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/messages/sync")
async def sync_chat_messages(
    chat_id: int,
    msg_ids: str = Query(..., description="ID сообщений через запятую"),
    ticket_id: Optional[int] = Query(
        None, description="ID тикета: только сообщения этого тикета"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Актуальное состояние сообщений для поллинга (редактирование/удаление собеседником)."""
    try:
        ids = [int(x.strip()) for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid msg_ids")
    if not ids:
        return {"messages": []}
    if len(ids) > 200:
        raise HTTPException(status_code=400, detail="Too many msg_ids (max 200)")

    messages = await get_messages_by_ids(
        db, chat_id=chat_id, operator=operator, msg_ids=ids, ticket_id=ticket_id,
    )
    return {"messages": messages}


# ───────────────────────────────────────────────
# POST /chats/{chat_id}/messages/read — отметить как прочитанное
# ───────────────────────────────────────────────
@router.post("/chats/{chat_id}/messages/read")
async def mark_messages_as_read(
    chat_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Отметить сообщение как прочитанное (и записать в user_mail_reads)."""
    message_ids = payload.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    reader_user_id = operator.get("user_id")
    if not reader_user_id:
        return {"status": "ok"}
    person_type = payload.get("person_type", "skystream")
    result = await mark_as_read(db, message_ids, reader_user_id, person_type)
    # Сбрасываем кэш счётчика непрочитанных чатов, чтобы навигация обновилась сразу.
    try:
        await redis_client.delete(f"unread_stats:{reader_user_id}")
    except Exception:
        pass
    return result


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/{msg_id}/preview — превью сообщения из другого тикета
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/messages/{msg_id}/preview")
async def message_preview(
    chat_id: int,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Превью одного сообщения по id (для отображения в модалке, когда сообщение не в текущем тикете)."""
    preview = await get_message_preview(db, chat_id, msg_id, operator)
    if not preview:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return preview


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/reads — пакетные прочтения (поллинг)
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/messages/reads")
async def messages_reads_batch(
    chat_id: int,
    msg_ids: str = Query(..., description="ID сообщений через запятую"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Пакетные прочтения для поллинга (свои сообщения в LK-тикете)."""
    try:
        ids = [int(x.strip()) for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid msg_ids")
    if not ids:
        return {}
    if len(ids) > 200:
        raise HTTPException(status_code=400, detail="Too many msg_ids (max 200)")
    return await get_messages_reads_batch(db, ids)


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/{msg_id}/reads — кто прочитал сообщение
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/messages/{msg_id}/reads")
async def message_reads(
    chat_id: int,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список читателей сообщения (для галочек «прочитано»)."""
    reads = await get_message_reads(db, msg_id)
    return {"reads": reads}


# ───────────────────────────────────────────────
# GET /chats/{chat_id}/messages/attachments/{attachment_id}/download
# ───────────────────────────────────────────────
@router.get("/chats/{chat_id}/messages/attachments/{attachment_id}/download")
async def download_chat_message_attachment(
    chat_id: int,
    attachment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Скачать вложение user_mail по id."""
    disk, filename, media_type = await resolve_mail_attachment_download(
        db, attachment_id=attachment_id, chat_id=chat_id,
    )
    return tracker_attachment_file_response(disk, filename, media_type)


# ───────────────────────────────────────────────
# DELETE /chats/{chat_id}/messages/{msg_id}/attachments/{attachment_id} — удалить вложение
# ───────────────────────────────────────────────
@router.delete("/chats/{chat_id}/messages/{msg_id}/attachments/{attachment_id}")
async def delete_message_attachment(
    chat_id: int,
    msg_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удалить вложение из сообщения (файл с диска и запись в БД)."""
    ok = await delete_chat_attachment(db, attachment_id=attachment_id, msg_id=msg_id, chat_id=chat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Вложение не найдено")
    return {"status": "deleted"}


# ───────────────────────────────────────────────
# PUT /chats/{chat_id}/messages/{msg_id} — редактирование
# ───────────────────────────────────────────────
@router.put("/chats/{chat_id}/messages/{msg_id}")
async def update_message(
    chat_id: int,
    msg_id: int,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Обновить сообщение в чате"""
    await UserMailDAO.update(db, filter_by={'id': msg_id}, text_=body['text'])
    return True


# ───────────────────────────────────────────────
# DELETE /chats/{chat_id}/messages/{msg_id} — удаление
# ───────────────────────────────────────────────
@router.delete("/chats/{chat_id}/messages/{msg_id}")
async def delete_message(
    chat_id: int,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удалить сообщение из чата"""
    await UserMailDAO.delete(db, id=msg_id)
    return {"status": "deleted"}


####################################
### Работа с трекером и тикетами ###
####################################

# ───────────────────────────────────────────────
# GET /chat/{chat_id}/selected_msg — выбор диапазона для тикета
# ───────────────────────────────────────────────
@router.get("/chat/{chat_id}/selected_msg", response_model=List[ChatMessageDTO])
async def get_selected_chat_messages(
    chat_id: int,
    start_id: int = Query(...),
    end_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Получить сообщения для контекста присоздании тикета"""
    return await get_user_messages_for_ticket(
        db, user_id=chat_id, start_id=start_id, end_id=end_id
    )


# ───────────────────────────────────────────────
# GET /tracker/{ticket_id}/history — история тикета (JSON)
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/station-info")
async def get_ticket_station_info(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    db_zabbix: Optional[AsyncSession] = Depends(get_db_zabbix_optional),
    operator: Dict = Depends(allow_support),
):
    """
    Информация по объекту (станции) для тикета с object_type='station'.
    ID объекта — station_id (wifitochka.ip_group). Название через StationFormsDAO.get_station_name().
    Метрики: уровень сигнала, бит/гц (последнее время), абоненты, число открытых тикетов по станции.
    """
    ticket_row = await db.execute(
        text("SELECT object_type, station_id FROM users.tracker_tickets WHERE id = :tid"),
        {"tid": ticket_id},
    )
    row = ticket_row.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if (row.get("object_type") or "user") != "station":
        raise HTTPException(
            status_code=400, detail="Тикет не относится к станции")

    station_id = row.get("station_id")
    if not station_id:
        return {"station_id": None, "station_name": None, "is_online": False, "last_online": None, "vno_name": None, "metrics": {}, "equipment": {}, "address": None, "master": None, "master_phone": None}

    station_name = await StationFormsDAO.get_station_name(session=db, station_id=station_id)
    if not station_name:
        station_name = f"Станция #{station_id}"

    station_group = await IpGroupDAO.find_one_or_none(session=db, id=station_id)
    if not station_group:
        return {"station_id": station_id, "station_name": station_name, "is_online": False, "last_online": None, "vno_name": None, "metrics": {}, "equipment": {}, "address": None, "master": None, "master_phone": None}

    # Статус онлайн/офлайн из stations.aliveness_status
    aliveness = await AlivenessStatusDAO.find_one_or_none(session=db, station_id=station_id)
    is_online = bool(aliveness.get("is_alive")) if aliveness else False
    last_online = aliveness.get("updated_at").isoformat(
    ) if aliveness and aliveness.get("updated_at") else None

    # VNO: название из таблицы VNO (name), не ID
    vno_name = None
    vno_id = station_group.get("vno")
    if vno_id:
        vno_row = await VirtualNetworkOperatorDAO.find_one_or_none(session=db, id=vno_id)
        vno_name = (vno_row.get("name") or "—") if vno_row else "—"

    ig = dict(station_group)
    parts = [ig.get("city"), ig.get("district"),
             ig.get("street"), ig.get("house")]
    address = ", ".join(p for p in parts if p) or None

    sf = await StationFormsDAO.find_one_or_none(session=db, station_id=station_id)
    equipment: Dict[str, Any] = {}
    master = None
    master_phone = None
    if sf:
        if sf.get("antenna_diameter") is not None:
            equipment["antenna_diameter"] = sf["antenna_diameter"]
        if sf.get("buc_power") is not None:
            equipment["buc_power"] = sf["buc_power"]
        if sf.get("modem_model"):
            equipment["modem_model"] = sf["modem_model"]
        elif sf.get("modem_brand"):
            equipment["modem_model"] = sf["modem_brand"]
        if sf.get("router_brand"):
            equipment["router_brand"] = sf["router_brand"]
        if sf.get("station_address"):
            address = sf["station_address"]
        master = sf.get("station_master") or None
        master_phone = sf.get("station_master_phone") or None

    # IP модема/роутера и подсети из ip_group
    if station_group.get("modem"):
        equipment["modem_ip"] = str(station_group["modem"])
    if station_group.get("router_ip"):
        equipment["router_ip"] = str(station_group["router_ip"])
    if station_group.get("network_hotspot"):
        equipment["network_hotspot"] = str(station_group["network_hotspot"])
    if station_group.get("network_pppoe"):
        equipment["network_pppoe"] = str(station_group["network_pppoe"])

    metrics: Dict[str, Any] = {}

    # Абоненты: всего, с тарифами, онлайн (как в профиле станции)
    try:
        users_info = await get_users_short_info(db, operator, station_id)
        metrics["subscribers_total"] = users_info.get("total", 0)
        metrics["subscribers_with_tariff"] = users_info.get("with_tariff", 0)
        metrics["subscribers_online"] = users_info.get("online", 0)
    except Exception:
        pass

    # Уровень сигнала и Бит/Гц как в таблице станций профиля партнёра: MonthlyStationStats + пороги для цвета
    yearmonth = get_yesterday_ym()
    stats = await MonthlyStationStatsDAO.find_one_or_none(session=db, station_id=station_id, yearmonth=yearmonth)
    channel_id = station_group.get("channel_id")
    antenna_size = (sf.get("antenna_diameter")
                    if sf else None) or station_group.get("antenna_cm_")
    thresholds: List[Dict[str, Any]] = []
    if channel_id and antenna_size is not None:
        try:
            ant_int = int(antenna_size)
            thresholds = await SatelliteThresholdsDAO.find_all(session=db, satellite=channel_id, antenna_size=ant_int) or []
        except (TypeError, ValueError):
            pass
    if stats:
        def _f(v):
            return round(float(v), 2) if v is not None else None
        avg_signal = _f(stats.get("avg_signal"))
        avg_signal_1d = _f(stats.get("avg_signal_1d"))
        avg_signal_7d = _f(stats.get("avg_signal_7d"))
        avg_bit_hz = _f(stats.get("avg_bit_hz"))
        avg_bit_hz_1d = _f(stats.get("avg_bit_hz_1d"))
        avg_bit_hz_7d = _f(stats.get("avg_bit_hz_7d"))
        metrics["signal_level"] = avg_signal
        metrics["signal_avg_1d"] = avg_signal_1d
        metrics["signal_avg_7d"] = avg_signal_7d
        metrics["signal_status"] = define_signal_and_bytegz_status(
            thresholds, "signal", avg_signal)
        metrics["bit_per_hz"] = avg_bit_hz
        metrics["bit_per_hz_1d"] = avg_bit_hz_1d
        metrics["bit_per_hz_7d"] = avg_bit_hz_7d
        metrics["bit_per_hz_status"] = define_signal_and_bytegz_status(
            thresholds, "bit_per_hz", avg_bit_hz)
    # Дополнительно: данные за последнее время из Zabbix (если нет MonthlyStationStats или для свежего значения)
    if db_zabbix and (not stats or metrics.get("signal_level") is None):
        try:
            zabbix = await get_last_hour_metrics(db, db_zabbix, operator, station_group)
            if zabbix.get("has_signal") and zabbix.get("avg_signal") is not None:
                metrics["signal_level"] = round(float(zabbix["avg_signal"]), 1)
                metrics["signal_level_last_time"] = zabbix.get(
                    "last_signal_time").isoformat() if zabbix.get("last_signal_time") else None
            if zabbix.get("has_bytegz") and zabbix.get("avg_bytegz") is not None:
                metrics["bit_per_hz"] = zabbix["avg_bytegz"]
                metrics["bit_per_hz_last_time"] = zabbix.get(
                    "last_bytegz_time").isoformat() if zabbix.get("last_bytegz_time") else None
        except Exception:
            pass

    # Число открытых тикетов по данной станции (object_type='station', station_id=X)
    try:
        open_statuses = ", ".join(f"'{s}'" for s in TRACKER_OPEN_STATUSES)
        cnt_res = await db.execute(
            text(f"""
                SELECT COUNT(*) AS cnt FROM users.tracker_tickets
                WHERE object_type = 'station' AND station_id = :sid AND status IN ({open_statuses})
            """),
            {"sid": station_id},
        )
        cnt_row = cnt_res.mappings().first()
        metrics["open_tickets_count"] = int(cnt_row["cnt"]) if cnt_row else 0
    except Exception:
        metrics["open_tickets_count"] = 0

    return {
        "station_id": station_id,
        "station_name": station_name,
        "is_online": is_online,
        "last_online": last_online,
        "vno_name": vno_name,
        "metrics": metrics,
        "equipment": equipment,
        "address": address,
        "master": master,
        "master_phone": master_phone,
    }


# ───────────────────────────────────────────────
# GET /tracker/{ticket_id}/history — жизненный цикл тикета
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/history")
async def get_ticket_history_api(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Жизненный цикл тикета: таймлайн и статистика."""
    history_data = await get_ticket_history_data(db, ticket_id)
    if history_data is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return history_data


# ───────────────────────────────────────────────
# GET /tracker/{ticket_id}/comments — внутренние комментарии по тикету
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/comments")
async def get_ticket_internal_comments(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список внутренних комментариев (чат между инженерами)."""
    # Проверка существования тикета
    r = await db.execute(text("SELECT 1 FROM users.tracker_tickets WHERE id = :tid"), {"tid": ticket_id})
    if not r.scalar():
        raise HTTPException(status_code=404, detail="Тикет не найден")
    result = await db.execute(
        text("""
            SELECT c.id, c.ticket_id, c.author_id, c.text, c.created_at,
                   au.full_name AS author_name
            FROM users.tracker_comments c
            JOIN users.skystream_users au ON au.id = c.author_id
            WHERE c.ticket_id = :ticket_id
            ORDER BY c.created_at ASC
        """),
        {"ticket_id": ticket_id},
    )
    rows = result.mappings().all()
    tz = pytz.timezone("Europe/Moscow")
    return [
        {
            "id": r["id"],
            "ticket_id": r["ticket_id"],
            "author_id": r["author_id"],
            "author_name": (r["author_name"] or "").strip(),
            "text": r["text"] or "",
            "created_at": r["created_at"].astimezone(tz).strftime("%d.%m.%Y %H:%M") if r["created_at"] else "",
        }
        for r in rows
    ]


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/comments — добавить внутренний комментарий
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/comments")
async def create_ticket_internal_comment(
    ticket_id: int,
    body: InternalCommentCreate,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Добавить внутренний комментарий к тикету."""
    author_id = operator.get("user_id")
    if not author_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    r = await db.execute(text("SELECT 1 FROM users.tracker_tickets WHERE id = :tid"), {"tid": ticket_id})
    if not r.scalar():
        raise HTTPException(status_code=404, detail="Тикет не найден")
    text_clean = (body.text or "").strip()
    if not text_clean:
        raise HTTPException(
            status_code=400, detail="Текст комментария не может быть пустым")
    result = await db.execute(
        text("""
            INSERT INTO users.tracker_comments (ticket_id, author_id, text)
            VALUES (:ticket_id, :author_id, :text)
            RETURNING id, ticket_id, author_id, text, created_at
        """),
        {"ticket_id": ticket_id, "author_id": author_id, "text": text_clean},
    )
    row = result.mappings().first()
    await db.commit()
    tz = pytz.timezone("Europe/Moscow")
    r_au = await db.execute(
        text("SELECT full_name FROM users.skystream_users WHERE id = :aid"),
        {"aid": author_id},
    )
    au_row = r_au.mappings().first()
    author_name = (au_row["full_name"] or "").strip(
    ) if au_row else f"ID {author_id}"
    return {
        "id": row["id"],
        "ticket_id": row["ticket_id"],
        "author_id": row["author_id"],
        "author_name": author_name,
        "text": row["text"],
        "created_at": row["created_at"].astimezone(tz).strftime("%d.%m.%Y %H:%M") if row["created_at"] else "",
    }


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/comments/{comment_id} — редактировать комментарий (только автор)
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/comments/{comment_id}")
async def update_ticket_internal_comment(
    ticket_id: int,
    comment_id: int,
    body: InternalCommentCreate,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Редактировать внутренний комментарий. Только автор."""
    author_id = operator.get("user_id")
    if not author_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    text_clean = (body.text or "").strip()
    if not text_clean:
        raise HTTPException(
            status_code=400, detail="Текст комментария не может быть пустым")
    r = await db.execute(
        text("SELECT author_id FROM users.tracker_comments WHERE id = :cid AND ticket_id = :tid"),
        {"cid": comment_id, "tid": ticket_id},
    )
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    if row["author_id"] != author_id:
        raise HTTPException(
            status_code=403, detail="Редактировать можно только свой комментарий")
    await db.execute(
        text("UPDATE users.tracker_comments SET text = :text WHERE id = :cid AND ticket_id = :tid"),
        {"text": text_clean, "cid": comment_id, "tid": ticket_id},
    )
    await db.commit()
    return {"id": comment_id, "text": text_clean}


# ───────────────────────────────────────────────
# DELETE /tracker/{ticket_id}/comments/{comment_id} — удалить комментарий (только автор)
# ───────────────────────────────────────────────
@router.delete("/tracker/{ticket_id}/comments/{comment_id}")
async def delete_ticket_internal_comment(
    ticket_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удалить внутренний комментарий. Только автор."""
    author_id = operator.get("user_id")
    if not author_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    r = await db.execute(
        text("SELECT author_id FROM users.tracker_comments WHERE id = :cid AND ticket_id = :tid"),
        {"cid": comment_id, "tid": ticket_id},
    )
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    if row["author_id"] != author_id:
        raise HTTPException(
            status_code=403, detail="Удалить можно только свой комментарий")
    await db.execute(
        text("DELETE FROM users.tracker_comments WHERE id = :cid AND ticket_id = :tid"),
        {"cid": comment_id, "tid": ticket_id},
    )
    await db.commit()
    return {"status": "deleted"}


# ───────────────────────────────────────────────
# GET /tracker/engineers — список инженеров (role=engineer) для фильтров
# ───────────────────────────────────────────────


@router.get("/tracker/filters/stations")
async def get_tracker_filters_stations(
    request: Request,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список станций для фильтра тикетов (ip_group, активные). Опционально ?search= для поиска по названию/партнёру."""
    search = request.query_params.get("search", "").strip()
    role = operator.get("role") or ""
    show_partner = role != "support"
    params: Dict[str, Any] = {}
    search_cond = ""
    if search:
        search_cond = " AND (COALESCE(sf.station_name, ig.name) ILIKE :search OR d.fullname ILIKE :search)"
        params["search"] = f"%{search}%"
    if show_partner:
        sql = text("""
            SELECT ig.id,
                   COALESCE(sf.station_name, ig.name) AS name,
                   d.fullname AS partner_name
            FROM wifitochka.ip_group ig
            LEFT JOIN LATERAL (
                SELECT station_id, partner, station_name
                FROM stations.station_forms
                WHERE station_id = ig.id
                LIMIT 1
            ) sf ON true
            LEFT JOIN partner.diler d ON d.id = sf.partner
            WHERE (ig.active = 1 OR ig.test_group = 1)
            """ + search_cond + """
            ORDER BY (COALESCE(sf.station_name, ig.name) ~ '^[А-Яа-яЁё]') DESC NULLS LAST,
                     COALESCE(sf.station_name, ig.name) NULLS LAST,
                     ig.id
            LIMIT 50
        """)
    else:
        search_cond_support = " AND (COALESCE(sf.station_name, ig.name) ILIKE :search)" if search else ""
        sql = text("""
            SELECT ig.id,
                   COALESCE(sf.station_name, ig.name) AS name
            FROM wifitochka.ip_group ig
            LEFT JOIN LATERAL (
                SELECT station_id, station_name
                FROM stations.station_forms
                WHERE station_id = ig.id
                LIMIT 1
            ) sf ON true
            WHERE (ig.active = 1 OR ig.test_group = 1)
            """ + search_cond_support + """
            ORDER BY (COALESCE(sf.station_name, ig.name) ~ '^[А-Яа-яЁё]') DESC NULLS LAST,
                     COALESCE(sf.station_name, ig.name) NULLS LAST,
                     ig.id
            LIMIT 50
        """)
    result = await db.execute(sql, params)
    rows = result.mappings().all()
    out = []
    for r in rows:
        name = (r["name"] or f"ID {r['id']}").strip()
        if show_partner and r.get("partner_name"):
            name = f"{name} — {r['partner_name'].strip()}"
        out.append({"id": r["id"], "name": name})
    return out


@router.get("/tracker/filters/hotspots")
async def get_tracker_filters_hotspots(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список бортов (hotspot) для фильтра тикетов."""
    sql = text("""
        SELECT id, name FROM stations.hotspot
        WHERE active = true
        ORDER BY name NULLS LAST, id
    """)
    result = await db.execute(sql)
    rows = result.mappings().all()
    return [{"id": r["id"], "name": (r["name"] or f"ID {r['id']}").strip()} for r in rows]


@router.get("/tracker/filters/vnos")
async def get_tracker_filters_vnos(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список VNO для фильтра тикетов."""
    sql = text("""
        SELECT id, name FROM wifitochka.virtual_network_operator
        ORDER BY name NULLS LAST, id
    """)
    result = await db.execute(sql)
    rows = result.mappings().all()
    return [{"id": r["id"], "name": (r["name"] or f"ID {r['id']}").strip()} for r in rows]


@router.get("/tracker/engineers")
async def get_tracker_engineers(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список пользователей с role=engineer из users.skystream_users (id, full_name)."""
    result = await db.execute(
        text("SELECT id, full_name FROM users.skystream_users WHERE role = 'engineer' ORDER BY full_name NULLS LAST, id")
    )
    rows = result.mappings().all()
    return [{"id": r["id"], "full_name": r["full_name"] or ""} for r in rows]


@router.get("/tracker/engineers-by-line")
async def get_tracker_engineers_by_line(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список инженеров (skystream_users: role = 'engineer' и level IN (1, 2)) для добавления исполнителя к тикету."""
    result = await db.execute(
        text("SELECT id, full_name FROM users.skystream_users WHERE role = 'engineer' AND level IN (1, 2) ORDER BY full_name NULLS LAST, id")
    )
    rows = result.mappings().all()
    return [{"id": r["id"], "full_name": r["full_name"] or ""} for r in rows]


@router.get("/tracker/{ticket_id}/executors")
async def get_ticket_executors(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список дополнительных исполнителей по тикету (tracker_ticket_executors)."""
    result = await db.execute(
        text("""
            SELECT e.abs_user_id AS id, au.full_name,
                   TO_CHAR(e.created_at, 'DD.MM.YYYY HH24:MI') AS added_at
            FROM users.tracker_ticket_executors e
            JOIN users.skystream_users au ON au.id = e.abs_user_id
            WHERE e.ticket_id = :ticket_id
            ORDER BY e.created_at, au.full_name NULLS LAST, e.abs_user_id
        """),
        {"ticket_id": ticket_id},
    )
    rows = result.mappings().all()
    return [{"id": r["id"], "full_name": (r["full_name"] or "").strip(), "added_at": r.get("added_at")} for r in rows]


@router.post("/tracker/{ticket_id}/executors")
async def add_ticket_executor(
    ticket_id: int,
    body: AddTicketExecutorSchema,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Добавить дополнительного исполнителя к тикету."""
    from app.api.v1.routers.helpdesk.dao import TrackerTicketExecutorsDAO

    abs_user_id = body.abs_user_id
    try:
        await TrackerTicketExecutorsDAO.add(db, ticket_id=ticket_id, abs_user_id=abs_user_id, auto_commit=False)
        await TrackerTicketLineHistoryDAO.add_event(
            db,
            ticket_id=ticket_id,
            event_type='executor_added',
            changed_by=operator.get('user_id'),
            payload={'abs_user_id': abs_user_id},
            auto_commit=False,
        )
        await db.commit()
        # Вернуть дату добавления для отображения без перезагрузки
        r = await db.execute(
            text("SELECT TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI') AS added_at FROM users.tracker_ticket_executors WHERE ticket_id = :ticket_id AND abs_user_id = :abs_user_id"),
            {"ticket_id": ticket_id, "abs_user_id": abs_user_id},
        )
        row = r.mappings().first()
        added_at = row["added_at"] if row else None
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409, detail="Исполнитель уже добавлен")
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "abs_user_id": abs_user_id, "added_at": added_at}


@router.delete("/tracker/{ticket_id}/executors/{abs_user_id}")
async def remove_ticket_executor(
    ticket_id: int,
    abs_user_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удалить дополнительного исполнителя из тикета. Основного (engineer_id) удалить нельзя."""
    from app.api.v1.routers.helpdesk.dao import TrackerTicketsDAO, TrackerTicketExecutorsDAO

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if ticket.get("engineer_id") == abs_user_id:
        raise HTTPException(
            status_code=400, detail="Нельзя удалить основного исполнителя")
    await TrackerTicketLineHistoryDAO.add_event(
        db,
        ticket_id=ticket_id,
        event_type='executor_removed',
        changed_by=operator.get('user_id'),
        payload={'abs_user_id': abs_user_id},
        auto_commit=False,
    )
    deleted = await TrackerTicketExecutorsDAO.delete(
        db, ticket_id=ticket_id, abs_user_id=abs_user_id, auto_commit=False
    )
    if deleted == 0:
        await db.rollback()
        raise HTTPException(
            status_code=404, detail="Исполнитель не найден в списке дополнительных")
    await db.commit()
    return Response(status_code=204)


# ───────────────────────────────────────────────
# Техники партнёра на тикете (tracker_ticket_technicians)
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/available-technicians")
async def get_available_technicians_for_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список техников партнёра, которых можно добавить к тикету (partner.technicians + technicians_partners)."""
    row = (await db.execute(
        text("""
            SELECT COALESCE(sf_p.partner, tt.author) AS partner_id
            FROM users.tracker_tickets tt
            LEFT JOIN stations.station_forms sf_p ON sf_p.station_id = COALESCE(tt.station_id, (SELECT u2.id_grp FROM users."user" u2 WHERE u2.id = tt.user_id AND tt.user_id IS NOT NULL LIMIT 1))
            WHERE tt.id = :tid AND COALESCE(tt.source, '') IN ('partner', 'tech')
        """),
        {"tid": ticket_id},
    )).mappings().first()
    if not row or row.get("partner_id") is None:
        return []
    partner_id = row["partner_id"]
    result = await db.execute(
        text("""
            SELECT t.technician_id AS id, t.full_name
            FROM partner.technicians t
            INNER JOIN partner.technicians_partners tp ON tp.technician_id = t.technician_id AND tp.partner_id = :partner_id
            ORDER BY t.full_name NULLS LAST, t.technician_id
        """),
        {"partner_id": partner_id},
    )
    rows = result.mappings().all()
    return [{"id": r["id"], "full_name": (r["full_name"] or "").strip() or f"Техник {r['id']}"} for r in rows]


@router.post("/tracker/{ticket_id}/technicians")
async def add_ticket_technician(
    ticket_id: int,
    body: AddTicketTechnicianSchema,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Добавить техника партнёра к тикету."""
    from app.api.v1.routers.helpdesk.dao import TrackerTicketTechniciansDAO

    technician_id = body.technician_id
    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    try:
        await TrackerTicketTechniciansDAO.add(db, ticket_id=ticket_id, technician_id=technician_id, auto_commit=False)
        await TrackerTicketLineHistoryDAO.add_event(
            db,
            ticket_id=ticket_id,
            event_type='technician_added',
            changed_by=operator.get('user_id'),
            payload={'technician_id': technician_id},
            auto_commit=False,
        )
        await db.commit()
        r = await db.execute(
            text("SELECT TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI') AS added_at FROM users.tracker_ticket_technicians WHERE ticket_id = :ticket_id AND technician_id = :technician_id"),
            {"ticket_id": ticket_id, "technician_id": technician_id},
        )
        row = r.mappings().first()
        added_at = row["added_at"] if row else None
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Техник уже добавлен")
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "technician_id": technician_id, "added_at": added_at}


@router.delete("/tracker/{ticket_id}/technicians/{technician_id}")
async def remove_ticket_technician(
    ticket_id: int,
    technician_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удалить техника из тикета."""
    from app.api.v1.routers.helpdesk.dao import TrackerTicketTechniciansDAO

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    await TrackerTicketLineHistoryDAO.add_event(
        db,
        ticket_id=ticket_id,
        event_type='technician_removed',
        changed_by=operator.get('user_id'),
        payload={'technician_id': technician_id},
        auto_commit=False,
    )
    deleted = await TrackerTicketTechniciansDAO.delete(
        db, ticket_id=ticket_id, technician_id=technician_id, auto_commit=False
    )
    if deleted == 0:
        await db.rollback()
        raise HTTPException(
            status_code=404, detail="Техник не найден в списке")
    await db.commit()
    return Response(status_code=204)


# ───────────────────────────────────────────────
# GET /tracker/list — список тикетов
# ───────────────────────────────────────────────
@router.get("/ticket-categories")
async def get_ticket_categories(
    support_line: Optional[int] = None,
    source: Optional[str] = None,
    tree: bool = False,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """
    Список активных категорий тикетов (users.ticket_categories).
    По умолчанию — плоский список с parent_id для построения дерева «родитель → дочерняя».
    tree=true — возвращает корневые категории (parent_id IS NULL) и в каждой вложенный список children.
    source — фильтр по источнику ('lk' для обычных, 'partner' для партнёрских).
    """
    q = "SELECT id, parent_id, name, slug, sla_minutes, support_line, complexity, priority, sort_order FROM users.ticket_categories WHERE is_active = true"
    params = {}
    if support_line is not None:
        q += " AND support_line = :support_line"
        params["support_line"] = support_line
    if source is not None:
        q += " AND source = :source"
        params["source"] = source
    q += " ORDER BY sort_order, name"
    result = await db.execute(text(q), params)
    rows = result.mappings().all()
    flat = [dict(r) for r in rows]
    if not tree:
        return flat
    by_id = {c["id"]: {**c, "children": []} for c in flat}
    roots = []
    for c in flat:
        node = by_id[c["id"]]
        if c["parent_id"] is None:
            roots.append(node)
        else:
            parent = by_id.get(c["parent_id"])
            if parent:
                parent["children"].append(node)
    return roots


# ───────────────────────────────────────────────
# GET /tracker/next — следующий открытый тикет для навигации
# ───────────────────────────────────────────────
@router.get("/tracker/next")
async def get_next_ticket(
    exclude: Optional[int] = Query(
        None, description="ID тикета, который нужно пропустить"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Следующий открытый тикет для кнопки «После отправки → Следующий тикет».

    Сортировка: приоритет (critical→high→middle→low) → закреплён за мной → дата создания ASC.
    Закрытые статусы (resolved / not_resolved / cancelled / closed) пропускаются.
    """
    user_id = operator.get("user_id")
    params: dict = {"uid": user_id}
    where_parts = [
        "tt.status NOT IN ('resolved', 'not_resolved', 'cancelled', 'closed')"]

    if exclude is not None:
        where_parts.append("tt.id != :excl")
        params["excl"] = exclude

    where_sql = " AND ".join(where_parts)

    sql = text(f"""
        SELECT tt.id
        FROM users.tracker_tickets tt
        WHERE {where_sql}
        ORDER BY
            CASE tt.priority
                WHEN 'critical' THEN 1
                WHEN 'high'     THEN 2
                WHEN 'middle'   THEN 3
                WHEN 'low'      THEN 4
                ELSE 5
            END ASC,
            CASE WHEN tt.engineer_id = :uid THEN 0 ELSE 1 END ASC,
            tt.date_of_create ASC
        LIMIT 1
    """)

    row = (await db.execute(sql, params)).fetchone()
    return {"id": row[0] if row else None}


@router.get("/tracker/views-counts")
async def get_views_counts(
    user: Dict = Depends(get_current_user),
    assigned_to: Optional[int] = None,
    unassigned: bool = False,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Счётчики для панели Views: по источникам и категориям (незакрытые тикеты)."""
    return await get_tracker_views_counts(db, assigned_to=assigned_to, unassigned=unassigned)


HELPDESK_NAV_CACHE_TTL = 10


async def _invalidate_helpdesk_redis_caches_after_tracker_mutation() -> None:
    """Сброс кэшей списка тикетов и счётчиков после мутаций (bulk и т.д.), иначе до 10 с отдаётся устаревший JSON из Redis."""
    prefixes = (
        "helpdesk_tracker_list:",
        "helpdesk_sidebar_counts:",
        "helpdesk_nav_tickets_count:",
        "helpdesk_partner_unread_count:",
    )
    for prefix in prefixes:
        try:
            async for key in redis_client.scan_iter(match=prefix + "*", count=256):
                await redis_client.delete(key)
        except Exception:
            pass


@router.get("/tracker/nav-tickets-count")
async def get_nav_tickets_count(
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support_marketing),
):
    """Количество тикетов «в работе» и тикетов с непрочитанными в чате. Кэш Redis 10 с — сначала из кэша, затем БД."""
    uid = user.get("user_id") or 0
    role = (operator.get("role") or "support").strip().lower()
    cache_key = f"helpdesk_nav_tickets_count:{uid}:{role}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    count = await get_helpdesk_nav_tickets_count(db, current_user_id=uid, role=role)
    unread_count = await get_helpdesk_nav_unread_tickets_count(db, current_user_id=uid, role=role)
    result = {"count": count, "unread_count": unread_count}
    try:
        await redis_client.setex(cache_key, HELPDESK_NAV_CACHE_TTL, json.dumps(result))
    except Exception:
        pass
    return result


@router.get("/tracker/partner-unread-count")
async def get_partner_unread_count(
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support_marketing),
):
    """Количество тикетов с непрочитанными в Партнерском кабинете. Кэш Redis 10 с — сначала из кэша, затем БД."""
    uid = user.get("user_id") or 0
    cache_key = f"helpdesk_partner_unread_count:{uid}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    count = await get_helpdesk_partner_unread_count(db, current_user_id=uid)
    result = {"count": count}
    try:
        await redis_client.setex(cache_key, HELPDESK_NAV_CACHE_TTL, json.dumps(result))
    except Exception:
        pass
    return result


@router.get("/tracker/sidebar-counts")
async def get_sidebar_counts(
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Счётчики для боковой панели тикетов. Кэш в Redis 10 с — один запрос в БД, остальные из кэша."""
    uid = user.get("user_id") or 0
    cache_key = f"helpdesk_sidebar_counts:{uid}:{(operator.get('role') or 'support').strip().lower()}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    result = await get_helpdesk_sidebar_counts(db, current_user_id=uid, role=operator.get("role"))
    try:
        await redis_client.setex(cache_key, 10, json.dumps(result))
    except Exception:
        pass
    return result


@router.get("/tracker/engineer-open-counts")
async def get_engineer_open_counts(
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Сводка: сколько открытых тикетов у каждого инженера и сколько без исполнителя. Кэш Redis 10с."""
    cache_key = "helpdesk_engineer_open_counts"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    open_statuses_sql = ", ".join(f"'{s}'" for s in TRACKER_OPEN_STATUSES)
    # Считаем по engineer_id (assigned_to на странице не используется)
    by_engineer_sql = text(f"""
        SELECT
            au.id AS engineer_id,
            COALESCE(NULLIF(TRIM(au.full_name), ''), 'ID ' || au.id::text) AS engineer_name,
            COUNT(*) AS cnt
        FROM users.tracker_tickets tt
        INNER JOIN users.skystream_users au ON au.id = tt.engineer_id
        WHERE tt.status IN ({open_statuses_sql})
        GROUP BY au.id, au.full_name
        ORDER BY cnt DESC, engineer_name ASC
    """)
    unassigned_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM users.tracker_tickets tt
        WHERE tt.status IN ({open_statuses_sql})
          AND tt.engineer_id IS NULL
    """)

    rows = (await db.execute(by_engineer_sql)).mappings().all()
    unassigned_row = (await db.execute(unassigned_sql)).mappings().first() or {}
    result = {
        "unassigned": int(unassigned_row.get("cnt") or 0),
        "engineers": [
            {
                "id": int(r["engineer_id"]),
                "name": r.get("engineer_name") or f"ID {r['engineer_id']}",
                "open": int(r.get("cnt") or 0),
            }
            for r in rows
            if r.get("engineer_id") is not None
        ],
    }

    try:
        await redis_client.setex(cache_key, 10, json.dumps(result))
    except Exception:
        pass
    return result


@router.get("/tracker/list")
async def get_tracker_tickets(
    user: Dict = Depends(get_current_user),
    all_statuses: bool = False,
    closed: bool = False,
    page: int = 1,
    per_page: int = 25,
    incidents_scope: Optional[str] = Query(
        None,
        description="Профиль абонента: active | closed (только с user_id и all_statuses)",
    ),
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    support_line: str = "",
    priority: str = "",
    category_id: Optional[int] = None,
    station: Optional[int] = None,
    q: str = "",
    date_create_from: Optional[str] = None,
    date_create_to: Optional[str] = None,
    date_close_from: Optional[str] = None,
    date_close_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    assigned_to: Optional[int] = None,
    closed_by: Optional[int] = None,
    hotspot_id: Optional[int] = None,
    vno: Optional[int] = None,
    status: Optional[str] = None,
    unassigned: bool = False,
    source: Optional[str] = None,
    section: Optional[int] = None,
    view: Optional[str] = None,
    since: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Список тикетов с поддержкой фильтра по абоненту, датам, исполнителю, закрывшему и борту. section/view — представление боковой панели. since — ISO datetime для поллинга: вернуть только тикеты созданные/обновлённые после since (и total). Ответ кэшируется в Redis: без since — 10 с; с since — 6 с (общий кэш поллинга для всех просматривающих страницу)."""
    role = user.get('role')
    uid = user.get("user_id") or 0

    eff_incidents_scope: Optional[str] = None
    if user_id is not None and all_statuses:
        eff_incidents_scope = incidents_scope if incidents_scope in ("active", "closed") else "active"

    def _list_cache_key() -> str:
        key = f"helpdesk_tracker_list:{section or 1}:{view or 'all_open'}:{page}:{per_page}"
        key += f":role:{(role or 'user').strip().lower()}"
        key += f":uid:{uid}"
        if since:
            key += f":since:{since}"
        if view == "mine":
            key += ":mine"
        if status:
            key += f":status:{status}"
        if category_id is not None:
            key += f":cat:{category_id}"
        if user_id is not None:
            key += f":uid:{user_id}"
            if all_statuses and eff_incidents_scope:
                key += f":inc:{eff_incidents_scope}"
        if station is not None:
            key += f":st:{station}"
        if assigned_to is not None:
            key += f":a:{assigned_to}"
        if hotspot_id is not None:
            key += f":h:{hotspot_id}"
        if vno is not None:
            key += f":v:{vno}"
        if sort_by:
            key += f":sort:{sort_by}:{sort_order or 'asc'}"
        return key

    cache_key = _list_cache_key()
    cache_ttl = 6 if since else 10
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    # Представление боковой панели (секция 1 и 3) переопределяет closed/status
    if section in (1, 3) and view in ("closed", "deferred"):
        closed = True
        if view == "deferred":
            status = "deferred"
    filters = {
        "user_id": user_id,
        "user_name": user_name.strip() if user_name else None,
        "support_line": support_line,
        "priority": priority,
        "station": station,
        "category_id": category_id,
        "source": source or None,
        "q": q,
        "section": section,
        "view": view,
        "current_user_id": user.get("user_id"),
    }
    if eff_incidents_scope is not None:
        filters["user_profile_incidents_scope"] = eff_incidents_scope
    if since:
        filters["since"] = since
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if unassigned:
        filters["unassigned"] = True
    if closed_by:
        filters["closed_by"] = closed_by
    if hotspot_id:
        filters["hotspot_id"] = hotspot_id
    if vno is not None:
        filters["vno"] = vno
    if status:
        filters["status"] = status
    if date_create_from:
        filters["date_create_from"] = date_create_from
    if date_create_to:
        filters["date_create_to"] = date_create_to
    if closed:
        if date_close_from:
            filters["date_close_from"] = date_close_from
        if date_close_to:
            filters["date_close_to"] = date_close_to
        if sort_by == "resolution_time" and sort_order in ("asc", "desc"):
            filters["sort_by"] = sort_by
            filters["sort_order"] = sort_order
    if sort_by and sort_order and sort_by in ("id", "title", "created_at", "closed_at", "user_id", "category", "source", "priority", "status", "updated_at", "assigned_to", "station", "vno", "hotspot", "complexity") and sort_order in ("asc", "desc"):
        filters["sort_by"] = sort_by
        filters["sort_order"] = sort_order
    # В разделе «Тикеты по категориям» (section 1) role=support видит только source lk, ks, abs; остальные — в своих разделах
    if (role or "").strip().lower() == "support" and (section or 1) == 1:
        filters["source_in"] = ["lk", "call_center", "abs"]
    result = await get_tickets(
        db=db,
        user_role=role,
        closed=closed,
        page=page,
        per_page=per_page,
        all_statuses=all_statuses,
        filters=filters,
    )
    try:
        def _json_default(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            raise TypeError(type(obj).__name__)
        await redis_client.setex(cache_key, cache_ttl, json.dumps(result, default=_json_default))
    except Exception:
        pass
    return result


async def _get_subscriber_station_hotspot_vno(db: AsyncSession, user_id: Optional[int]):
    """По user_id абонента вернуть (station_id, hotspot_id, vno). station_id = id_grp из users.user."""
    if not user_id:
        return None, None, None
    r = await db.execute(
        text("""
            SELECT u.id_grp, ig.id_hotspot, ig.vno
            FROM users."user" u
            LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp AND u.id_grp IS NOT NULL AND u.id_grp != 0
            WHERE u.id = :uid
        """),
        {"uid": user_id},
    )
    row = r.mappings().first()
    if not row or row["id_grp"] is None:
        return None, None, None
    station_id = int(row["id_grp"])
    hotspot_id = int(row["id_hotspot"]) if row.get("id_hotspot") is not None else None
    vno = int(row["vno"]) if row.get("vno") is not None else None
    return station_id, hotspot_id, vno


# ───────────────────────────────────────────────
# POST /tracker/new — создание тикета
# ───────────────────────────────────────────────
@router.post("/tracker/new")
async def create_new_ticket(
    ticket: TicketCreateSchema,
    operator: Dict = Depends(require_ticket_create),
    db: AsyncSession = Depends(get_db),
):
    """Создаёт тикет в users.tracker_tickets. source=ks, support_line=2, person_type=skystream, object_type=user.
    По user_id абонента заполняет station_id, hotspot_id, vno из ip_group.
    sla_deadline и complexity берутся из users.ticket_categories для выбранной категории и support_line=2."""
    now = datetime.now(timezone.utc)
    user_id = operator.get('user_id')
    role = operator.get('role')
    station_id, hotspot_id, vno = await _get_subscriber_station_hotspot_vno(db, ticket.user_id)

    # SLA: минуты реакции из категории для линии 2
    sla_minutes = 60
    try:
        r = await db.execute(
            text("SELECT sla_minutes FROM users.ticket_categories WHERE id = :cid AND support_line = 2 AND is_active = true"),
            {"cid": ticket.category_id},
        )
        row = r.mappings().first()
        if row and row["sla_minutes"] is not None:
            sla_minutes = int(row["sla_minutes"])
    except Exception:
        pass
    sla_deadline = now + timedelta(minutes=sla_minutes)

    add_kw = dict(
        user_id=ticket.user_id,
        category_id=ticket.category_id,
        priority=ticket.priority,
        title=(ticket.title or "Обращение").strip() or "Обращение",
        body=ticket.body or None,
        author=user_id,
        updated_at=now,
        support_line=2,
        source="abs" if role == "engineer" else "ks",
        person_type="skystream",
        object_type="user",
        station_id=station_id,
        hotspot_id=hotspot_id,
        vno=vno,
        sla_deadline=sla_deadline,
        status="in_progress",
        engineer_id=user_id if role == "engineer" else None,
    )
    ticket_db = await TrackerTicketsDAO.add(db, **add_kw)

    now = now + timedelta(seconds=3)
    # Первая запись в истории: создание тикета + старт линии 2
    await TrackerTicketLineHistoryDAO.add(
        db,
        ticket_id=ticket_db['id'],
        support_line=2,
        start_time=now,
        changed_by=user_id,
        event_type='created',
        payload={'support_line': 2, 'status': 'in_progress'},
        auto_commit=False,
    )
    # Связь с письмами
    if ticket.msg_id_min:
        await TrackerTicketMailLinksDAO.add(db, ticket_id=ticket_db['id'], user_mail_id=ticket.msg_id_min)
        if ticket.msg_id_min != ticket.msg_id_max:
            await TrackerTicketMailLinksDAO.add(db, ticket_id=ticket_db['id'], user_mail_id=ticket.msg_id_max)
    return {"ticket_id": ticket_db['id'], "status": "created"}


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/message — новое сообщение
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/message")
async def create_message(
    ticket_id: int,
    msg: MessageCreate,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Сохранение сообщения в чате тикета"""
    user_id = operator.get('user_id')
    role = (operator.get('role') or '').lower()
    now = datetime.now(timezone.utc)
    message_data = await TrackerMessagesDAO.add(
        db,
        ticket_id=ticket_id,
        author_id=user_id,
        body=msg.text,
        created_at=now,
    )

    # Обновляем время обновления тикета
    await TrackerTicketsDAO.update(db, filter_by={'id': ticket_id}, updated_at=now)

    # Если инженер написал и не в тикете — назначить основным или добавить в исполнители
    participant_update = await ensure_engineer_participant_on_message(db, ticket_id, user_id, role)

    created_at = message_data.get('created_at') or now
    result = {
        "id": message_data['id'],
        "text": message_data['body'],
        "created_at": created_at.isoformat(),
        "author": operator.get('full_name', 'Вы'),
        "user_id": user_id,
        "is_own": True,
    }
    if participant_update:
        result.update(participant_update)
    return result


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/message/{msg_id} — редактирование
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/message/{msg_id}")
async def update_message(
    ticket_id: int,
    msg_id: int,
    msg: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Обновление сообщения в чате"""
    updated_at = datetime.now(timezone.utc)
    await TrackerMessagesDAO.update(
        db,
        filter_by={'id': msg_id, 'ticket_id': ticket_id},
        body=msg.text,
        updated_at=updated_at,
        is_edited=True,
    )
    return {"text": msg.text}


# ───────────────────────────────────────────────
# DELETE /tracker/{ticket_id}/message/{msg_id} — удаление
# ───────────────────────────────────────────────
@router.delete("/tracker/{ticket_id}/message/{msg_id}")
async def delete_message(
    ticket_id: int,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Удаление сообщения из чата"""
    deleted_count = await TrackerMessagesDAO.delete(
        db,
        id=msg_id,
        ticket_id=ticket_id,
    )
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"ok": True}


# ───────────────────────────────────────────────
# GET /tracker/{ticket_id}/poll — лёгкий поллинг изменений тикета
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/poll")
async def poll_ticket_updates(
    ticket_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Лёгкий эндпоинт для поллинга: статус тикета + max_msg_id в user_mail.

    Результат кэшируется в Redis на 5 секунд с ключом poll:ticket:{ticket_id}.
    Все операторы, смотрящие один тикет, получают ответ из одного кэша.
    Rate-limit не применяется (путь в cacheable_paths).
    """
    cache_key = f"poll:ticket:{ticket_id}"

    cached = await redis_client.get(cache_key)
    if cached:
        return Response(content=cached, media_type="application/json")

    row = await db.execute(
        text("SELECT status FROM users.tracker_tickets WHERE id = :id"),
        {"id": ticket_id},
    )
    ticket_row = row.fetchone()
    if not ticket_row:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    status_raw = ticket_row[0]

    max_id_row = await db.execute(
        text("SELECT COALESCE(MAX(id), 0) FROM users.user_mail WHERE ticket_id = :tid"),
        {"tid": ticket_id},
    )
    max_msg_id = int(max_id_row.scalar() or 0)

    result = {
        "status": status_raw,
        "status_label": STATUS_DISPLAY.get(status_raw, status_raw),
        "max_msg_id": max_msg_id,
        "is_open": status_raw in TRACKER_OPEN_STATUSES,
    }

    payload = json.dumps(result, ensure_ascii=False)
    try:
        await redis_client.setex(cache_key, 5, payload)
    except Exception:
        pass

    return Response(content=payload, media_type="application/json")


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/status — изменение статуса
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/status")
async def change_ticket_status(
    ticket_id: int,
    body: StatusUpdateSchema,
    background_tasks: BackgroundTasks,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Закрытие или переоткрытие тикета"""
    now = datetime.now(timezone.utc)
    user_id = operator.get('user_id')
    role = operator.get('role')
    line = 1 if role == 'support' else 2

    update_data = {'updated_at': now}

    if body.action == TicketStatusAction.CLOSE:
        if role not in ('engineer', 'director', 'admin'):
            raise HTTPException(
                status_code=403, detail="Закрыть тикет может только инженер")
        resolution = body.resolution or "resolved"
        if resolution not in ("resolved", "not_resolved", "cancelled"):
            resolution = "resolved"
        update_data.update({
            "status": resolution,
            "date_of_close": now,
            "closed_by": user_id,
        })
        ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
        if ticket and (ticket.get('engineer_id') is None or ticket.get('engineer_id') == 0) and role in ('engineer', 'director'):
            update_data["engineer_id"] = user_id
        response_status = STATUS_DISPLAY.get(resolution, "Решён")
        background_tasks.add_task(
            close_ticket_line_history, ticket_id=ticket_id, user_id=user_id, status=resolution)

    elif body.action == TicketStatusAction.REOPEN:
        ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
        if ticket:
            date_of_close = ticket.get('date_of_close')
            if date_of_close:
                if date_of_close.tzinfo is None:
                    date_of_close = date_of_close.replace(tzinfo=timezone.utc)
                elapsed_s = (now - date_of_close).total_seconds()
                if elapsed_s >= 72 * 3600:
                    raise HTTPException(
                        status_code=403,
                        detail="Нельзя переоткрыть тикет позже чем через 72 часа после закрытия"
                    )
        update_data.update({
            "status": "in_progress",
            "support_line": line,
            "date_of_close": None,
        })
        response_status = STATUS_DISPLAY.get("in_progress", "В работе")
        background_tasks.add_task(
            reopen_ticket_line_history, ticket_id=ticket_id, user_id=user_id)

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Выполняем обновление
    updated_rows = await TrackerTicketsDAO.update(
        db,
        filter_by={'id': ticket_id},
        **update_data
    )

    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    is_open = body.action == TicketStatusAction.REOPEN
    resp = {"status": response_status, "is_open": is_open}
    if is_open:
        resp["line"] = update_data.get("support_line", line)
    return resp


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/assign-engineer — назначить инженера по round-robin
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/assign-engineer")
async def assign_engineer_roundrobin(
    ticket_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Назначить инженера по round-robin.

    Доступно только для role=support и только если тикет ещё не закреплён.
    Выбирает инженера из skystream_users (role='engineer', level=1) циклически
    через Redis-счётчик rr:engineer_assign, гарантируя равномерное распределение.
    """
    op_role = operator.get("role", "")
    if op_role != "support":
        raise HTTPException(
            status_code=403, detail="Только КС может назначить инженера таким образом")

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if ticket.get("engineer_id"):
        raise HTTPException(
            status_code=400, detail="Тикет уже закреплён за инженером")

    # Список инженеров первой линии (level=1), отсортированных по id для стабильности
    eng_rows = await db.execute(
        text("""
            SELECT id, full_name
            FROM users.skystream_users
            WHERE role = 'engineer' AND level = 1
            ORDER BY id
        """)
    )
    engineers = eng_rows.fetchall()
    if not engineers:
        raise HTTPException(
            status_code=404, detail="Нет доступных инженеров (role=engineer, level=1)")

    # Round-robin через Redis: ключ общий для всей системы назначений
    _RR_KEY = "rr:engineer_assign"
    try:
        idx = int(await redis_client.incr(_RR_KEY))
    except Exception:
        idx = 1

    chosen = engineers[(idx - 1) % len(engineers)]
    chosen_id, chosen_name = chosen[0], chosen[1] or f"Инженер #{chosen[0]}"

    now = datetime.now(timezone.utc)
    await TrackerTicketsDAO.update(
        db,
        filter_by={"id": ticket_id},
        engineer_id=chosen_id,
        support_line=2,
        updated_at=now,
    )

    # Фиксируем смену линии в истории (функция открывает собственную сессию)
    await assign_new_line_history(
        ticket_id=ticket_id,
        user_id=operator.get("user_id"),
        new_line=2,
    )

    logger.info("assign-engineer round-robin: ticket %s → engineer %s (%s)",
                ticket_id, chosen_id, chosen_name)

    return {"assigned_to": chosen_id, "assigned_name": chosen_name}


# ───────────────────────────────────────────────
# POST /tracker/distribute-tickets — распределить тикеты без исполнителя по round-robin
# ───────────────────────────────────────────────
@router.post("/tracker/distribute-tickets")
async def distribute_tickets(
    body: DistributeTicketsSchema,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Распределяет тикеты/инциденты без исполнителя в выбранной секции/виде между инженерами level=1
    по round-robin. Секции 1,3 — tracker_tickets; секции 2,4 — monitoring.incidents.
    Роль support не может вызывать этот эндпоинт.
    """
    if operator.get("role") == "support":
        raise HTTPException(
            status_code=403, detail="Распределение тикетов недоступно для данной роли")
    result = await distribute_tickets_roundrobin(
        db,
        section=body.section,
        view=body.view,
        current_user_id=operator.get("user_id"),
        operator_id=operator.get("user_id"),
        background_tasks=background_tasks,
    )
    if result.get("distributed", 0) > 0:
        uid = operator.get("user_id")
        if uid is not None:
            try:
                await redis_client.delete(f"helpdesk_sidebar_counts:{uid}")
            except Exception:
                pass
    return result


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/assign — назначение линии
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    body: AssignmentUpdateSchema,
    background_tasks: BackgroundTasks,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Смена линии поддержки или назначение себе. Назначить тикет себе может только инженер."""
    role = operator.get('role')
    user_id = operator.get('user_id')

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    update_data = {'updated_at': datetime.now(timezone.utc)}

    # engineer_id — основной инженер, назначается один раз (первый «взять в работу» / первое сообщение).
    # assigned_to — представитель КС, закреплённый за тикетом.
    # Перемещение между линиями НЕ меняет engineer_id: инженер остаётся ответственным
    # до конца жизни тикета. Доп. инженеры — tracker_ticket_executors.
    if body.target == AssignmentTarget.CS:
        new_line = 1
    elif body.target == AssignmentTarget.ENGINEERS:
        new_line = 2
    elif body.target == AssignmentTarget.SELF:
        if role == 'support':
            new_line = 1
            if ticket and (ticket.get('assigned_to') is None or ticket.get('assigned_to') == 0):
                update_data['assigned_to'] = user_id
        elif role in ('engineer', 'director'):
            new_line = 2
            if ticket and (ticket.get('engineer_id') is None or ticket.get('engineer_id') == 0):
                update_data['engineer_id'] = user_id
                update_data['status'] = 'in_progress'
        else:
            raise HTTPException(
                status_code=403, detail="Назначить тикет себе может только инженер или КС")
    else:
        raise HTTPException(
            status_code=400, detail="Invalid assignment target")

    update_data['support_line'] = new_line

    updated_rows = await TrackerTicketsDAO.update(
        db,
        filter_by={'id': ticket_id},
        **update_data,
    )

    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    background_tasks.add_task(
        assign_new_line_history,
        ticket_id=ticket_id,
        user_id=user_id,
        new_line=new_line
    )

    return {
        "status": "Открыт",
        "line": new_line,
        "assigned_to": update_data.get("engineer_id") or update_data.get("assigned_to"),
    }


# ───────────────────────────────────────────────
# PATCH /tracker/bulk — массовое обновление (статус, категория, приоритет)
# ───────────────────────────────────────────────
ALLOWED_BULK_STATUSES = (
    "resolved", "not_resolved", "cancelled", "waiting_client", "waiting_cs",
    "waiting_technician", "no_technician", "waiting_parts", "in_progress", "deferred",
)


@router.patch("/tracker/bulk")
async def bulk_update_tracker_tickets(
    body: BulkTicketsUpdateSchema,
    background_tasks: BackgroundTasks,
    operator: Dict = Depends(allow_engineer),
    db: AsyncSession = Depends(get_db),
):
    """
    Обновление одного или нескольких тикетов: статус, категория, приоритет.
    Для одного тикета можно передать ticket_id, для нескольких — ticket_ids.
    """
    ids = body.get_ids()
    if not ids:
        raise HTTPException(
            status_code=400, detail="Укажите ticket_id или ticket_ids")
    if body.status is not None and body.status not in ALLOWED_BULK_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Недопустимый статус. Допустимы: {list(ALLOWED_BULK_STATUSES)}")
    if body.priority is not None and body.priority not in ("low", "middle", "high", "critical"):
        raise HTTPException(
            status_code=400, detail="Приоритет: low, middle, high, critical")
    if body.support_line is not None and body.support_line not in (1, 2, 3):
        raise HTTPException(
            status_code=400, detail="Линия ТП: 1 = КС, 2 = инженеры, 3 = партнёры")
    operator_id = operator.get("user_id")
    if not operator_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    result = await bulk_update_tickets(
        db,
        ticket_ids=ids,
        operator_id=operator_id,
        status=body.status,
        category_id=body.category_id,
        priority=body.priority,
        support_line=body.support_line,
        background_tasks=background_tasks,
    )
    await _invalidate_helpdesk_redis_caches_after_tracker_mutation()
    return result


# ───────────────────────────────────────────────
# DELETE /tracker/bulk — массовое удаление (только админ)
# ───────────────────────────────────────────────
@router.delete("/tracker/bulk")
async def bulk_delete_tracker_tickets(
    body: BulkTicketsDeleteSchema,
    operator: Dict = Depends(allow_admin),
    db: AsyncSession = Depends(get_db),
):
    """Удаление тикетов по списку ID. Доступно только администратору."""
    deleted = await bulk_delete_tickets(db, ticket_ids=body.ticket_ids)
    await _invalidate_helpdesk_redis_caches_after_tracker_mutation()
    return {"deleted": deleted}


#########################
### DATABASE HELPDESK ###
#########################

@router.get("/database/home", response_model=HomeResponse)
async def get_kb_home(
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Главная страница: Категории и Популярные вопросы"""

    # 1. Получаем корневые категории (BaseDAO)
    categories_data = await DBCategoryDAO.find_all(
        db,
        parent_id=None,
        order_by=DBCategory.order
    )

    # 2. Получаем популярные статьи (Кастомный метод или BaseDAO с сортировкой)
    popular_data = await DBArticleDAO.get_popular(db, limit=10)

    cats_dto = []
    for c in categories_data:
        # 3. Считаем кол-во статей. BaseDAO.count отлично подходит.
        count = await DBArticleDAO.count(db, category_id=c["id"])

        # Собираем DTO вручную или через Pydantic.
        # Т.к. DAO вернул dict, обращаемся по ключам c["id"], а не c.id
        c_dto = CategoryDTO(
            id=c["id"],
            name=c["name"],
            icon=c["icon"],
            color=c["color"],
            article_count=count
        )
        cats_dto.append(c_dto)

    return {"categories": cats_dto, "popular": popular_data}


@router.get("/database/categories/{cat_id}", response_model=ArticleListResponse)
async def get_category_articles(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Статьи в категории"""
    # Используем стандартный метод BaseDAO
    articles = await DBArticleDAO.find_all(db, category_id=cat_id)
    return {"articles": articles}


@router.get("/database/articles/{article_id}", response_model=ArticleDetailDTO)
async def get_article_tree(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Получение полного дерева решений для статьи"""

    # 1. Получаем статью
    article = await DBArticleDAO.find_one_or_none(db, id=article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")

    # 2. Увеличиваем просмотры (+1)
    # Используем update метод DAO.
    # Внимание: update принимает filter_by и данные для обновления
    new_view_count = article["view_count"] + 1
    await DBArticleDAO.update(db, filter_by={"id": article_id}, view_count=new_view_count)

    # 3. Выгружаем все узлы статьи (BaseDAO)
    # nodes будет списком словарей
    nodes = await DBNodeDAO.find_all(db, article_id=article_id)

    # 4. Собираем дерево в Python
    node_map = {}
    roots = []

    # Превращаем словари в DTO и кладем в map
    for node in nodes:
        # Важно: Pydantic v2 использует model_validate для словарей тоже (если from_attributes=True)
        dto = KBNodeDTO.model_validate(node)
        dto.children = []
        node_map[node["id"]] = {"dto": dto, "parent_id": node["parent_id"]}

    # Строим иерархию
    for node_id, item in node_map.items():
        dto = item["dto"]
        parent_id = item["parent_id"]

        if parent_id is None:
            roots.append(dto)  # Это корневой узел
        else:
            # Ищем родителя и добавляем себя к нему в дети
            if parent_id in node_map:
                node_map[parent_id]["dto"].children.append(dto)

    return {"id": article["id"], "title": article["title"], "tree": roots}


@router.get("/database/search", response_model=ArticleListResponse)
async def search_kb(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    operator: Dict = Depends(allow_support),
):
    """Поиск по названию и содержимому узлов"""
    if not q:
        return {"articles": []}

    # Используем кастомный метод DAO, так как BaseDAO не умеет в JOIN и ILIKE
    articles = await DBArticleDAO.search_complex(db, query_str=q)

    return {"articles": articles}


###################
### База знаний ###
###################

# # === КАТЕГОРИИ ===
# @router.get("/categories", response_model=List[Category])
# async def get_categories(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBCategory))
#     return result.scalars().all()

# @router.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
# async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
#     db_cat = DBCategory(**category.model_dump())
#     db.add(db_cat)
#     await db.commit()
#     await db.refresh(db_cat)
#     return db_cat

# @router.put("/categories/{category_id}", response_model=Category)
# async def update_category(category_id: int, category: CategoryUpdate, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBCategory).where(DBCategory.id == category_id))
#     db_cat = result.scalar_one_or_none()
#     if not db_cat:
#         raise HTTPException(status_code=404, detail="Категория не найдена")

#     for key, value in category.model_dump(exclude_unset=True).items():
#         setattr(db_cat, key, value)

#     await db.commit()
#     await db.refresh(db_cat)
#     return db_cat

# @router.delete("/categories/{category_id}")
# async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBCategory).where(DBCategory.id == category_id))
#     db_cat = result.scalar_one_or_none()
#     if not db_cat:
#         raise HTTPException(status_code=404, detail="Категория не найдена")

#     await db.execute(delete(DBCategory).where(DBCategory.id == category_id))
#     await db.commit()
#     return {"status": "ok"}

# # === СТАТЬИ ===
# @router.get("/articles", response_model=List[Article])
# async def get_articles(category_id: int = None, db: AsyncSession = Depends(get_db)):
#     query = select(DBArticle)
#     if category_id is not None:
#         query = query.where(DBArticle.category_id == category_id)
#     result = await db.execute(query)
#     return result.scalars().all()

# @router.post("/articles", response_model=Article, status_code=status.HTTP_201_CREATED)
# async def create_article(article: ArticleCreate, db: AsyncSession = Depends(get_db)):
#     db_art = DBArticle(**article.model_dump())
#     db.add(db_art)
#     await db.commit()
#     await db.refresh(db_art)
#     return db_art

# @router.put("/articles/{article_id}", response_model=Article)
# async def update_article(article_id: int, article: ArticleUpdate, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBArticle).where(DBArticle.id == article_id))
#     db_art = result.scalar_one_or_none()
#     if not db_art:
#         raise HTTPException(status_code=404, detail="Статья не найдена")

#     for key, value in article.model_dump(exclude_unset=True).items():
#         setattr(db_art, key, value)

#     await db.commit()
#     await db.refresh(db_art)
#     return db_art

# @router.delete("/articles/{article_id}")
# async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBArticle).where(DBArticle.id == article_id))
#     db_art = result.scalar_one_or_none()
#     if not db_art:
#         raise HTTPException(status_code=404, detail="Статья не найдена")

#     await db.execute(delete(DBArticle).where(DBArticle.id == article_id))
#     await db.commit()
#     return {"status": "ok"}

# # === УЗЛЫ ===
# @router.get("/articles/{article_id}/nodes", response_model=List[Node])
# async def get_nodes(article_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBNode).where(DBNode.article_id == article_id))
#     return result.scalars().all()

# @router.post("/nodes", response_model=Node, status_code=status.HTTP_201_CREATED)
# async def create_node(node: NodeCreate, db: AsyncSession = Depends(get_db)):
#     db_node = DBNode(**node.model_dump())
#     db.add(db_node)
#     await db.commit()
#     await db.refresh(db_node)
#     return db_node

# @router.put("/nodes/{node_id}", response_model=Node)
# async def update_node(node_id: int, node: NodeUpdate, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBNode).where(DBNode.id == node_id))
#     db_node = result.scalar_one_or_none()
#     if not db_node:
#         raise HTTPException(status_code=404, detail="Узел не найден")

#     for key, value in node.model_dump(exclude_unset=True).items():
#         setattr(db_node, key, value)

#     await db.commit()
#     await db.refresh(db_node)
#     return db_node

# @router.delete("/nodes/{node_id}")
# async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(DBNode).where(DBNode.id == node_id))
#     db_node = result.scalar_one_or_none()
#     if not db_node:
#         raise HTTPException(status_code=404, detail="Узел не найден")

#     await db.execute(delete(DBNode).where(DBNode.id == node_id))
#     await db.commit()
#     return {"status": "ok"}


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/link-user — привязать абонента к тикету
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/link-user")
async def link_user_to_ticket(
    ticket_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Привязать (или отвязать) абонента к тикету.

    Body: {"user_id": 123}  — привязать (дополнительно заполняются station_id, hotspot_id, vno из id_grp абонента)
          {"user_id": null} — отвязать (station_id, hotspot_id, vno обнуляются)
    """
    body = await request.json()
    user_id = body.get("user_id")

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    station_id: Optional[int] = None
    hotspot_id: Optional[int] = None
    vno: Optional[int] = None

    if user_id is not None:
        # id_grp абонента = station_id тикета; из ip_group по id_grp — hotspot_id, vno
        row = await db.execute(
            text("""
                SELECT u.id_grp, ig.id_hotspot, ig.vno
                FROM users."user" u
                LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp AND (u.id_grp IS NOT NULL AND u.id_grp != 0)
                WHERE u.id = :uid
            """),
            {"uid": user_id},
        )
        user_row = row.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="Абонент не найден")
        id_grp_val, hs, v = user_row
        if id_grp_val is not None and id_grp_val != 0:
            station_id = int(id_grp_val)
        if hs is not None:
            hotspot_id = int(hs)
        if v is not None:
            vno = int(v)

    update_kw: Dict[str, Any] = {
        "user_id": user_id,
        "station_id": station_id,
        "hotspot_id": hotspot_id,
        "vno": vno,
        "object_type": "user" if user_id is not None else "other",
        "updated_at": datetime.now(timezone.utc),
    }
    await TrackerTicketsDAO.update(db, filter_by={"id": ticket_id}, **update_kw)
    await db.commit()

    return {"user_id": user_id, "station_id": station_id, "hotspot_id": hotspot_id, "vno": vno}


# ───────────────────────────────────────────────
# PATCH /tracker/{ticket_id}/link-station — привязать тикет к станции (object_type=station)
# ───────────────────────────────────────────────
@router.patch("/tracker/{ticket_id}/link-station")
async def link_station_to_ticket(
    ticket_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Привязать тикет к станции (для object_type=other, source=partner).

    Body: {"station_id": 123} — привязать; station_id из wifitochka.ip_group.
    """
    body = await request.json()
    station_id = body.get("station_id")

    if station_id is None:
        raise HTTPException(status_code=400, detail="Укажите station_id")

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    row = await db.execute(
        text("""
            SELECT ig.id, ig.id_hotspot, ig.vno
            FROM wifitochka.ip_group ig
            WHERE ig.id = :sid
        """),
        {"sid": station_id},
    )
    station_row = row.fetchone()
    if not station_row:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    _, hotspot_id, vno = station_row
    update_kw: Dict[str, Any] = {
        "user_id": None,
        "station_id": int(station_id),
        "hotspot_id": int(hotspot_id) if hotspot_id is not None else None,
        "vno": int(vno) if vno is not None else None,
        "object_type": "station",
        "updated_at": datetime.now(timezone.utc),
    }
    await TrackerTicketsDAO.update(db, filter_by={"id": ticket_id}, **update_kw)
    await db.commit()

    return {"station_id": int(station_id), "hotspot_id": update_kw["hotspot_id"], "vno": update_kw["vno"]}


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/ks-transfer — смена линии для KS-тикетов
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/ks-transfer")
async def ks_transfer_line(
    ticket_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Смена линии ТП для тикетов с source=ks (и partner/tech).

    Направления:
    - to_engineers:      линия 1→2, round-robin назначение инженера, статус in_progress
    - to_cs:             линия 2→1, статус waiting_cs, engineer_id НЕ сбрасывается
    - to_engineers_self: линия 1→2, engineer берёт обратно (уже назначен), статус in_progress

    Все смены фиксируются в tracker_ticket_line_history.
    """
    body = await request.json()
    direction = body.get("direction", "")
    if direction not in ("to_engineers", "to_cs", "to_engineers_self"):
        raise HTTPException(status_code=400, detail="Неверное направление")

    role = operator.get("role", "")
    user_id = operator.get("user_id")
    now = datetime.now(timezone.utc)

    ticket = await TrackerTicketsDAO.find_one_or_none(db, id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    update_data: dict = {"updated_at": now}
    assigned_name: Optional[str] = None
    chosen_id: Optional[int] = None

    if direction == "to_engineers":
        if role != "support":
            raise HTTPException(
                status_code=403, detail="Только КС может передать тикет инженерам")

        eng_rows = await db.execute(text(
            "SELECT id, full_name FROM users.skystream_users "
            "WHERE role = 'engineer' AND level = 1 ORDER BY id"
        ))
        engineers = eng_rows.fetchall()
        if not engineers:
            raise HTTPException(
                status_code=404, detail="Нет доступных инженеров (role=engineer, level=1)")

        _RR_KEY = "rr:engineer_assign"
        try:
            idx = int(await redis_client.incr(_RR_KEY))
        except Exception:
            idx = 1
        chosen = engineers[(idx - 1) % len(engineers)]
        chosen_id = chosen[0]
        assigned_name = chosen[1] or f"Инженер #{chosen_id}"

        update_data.update(
            {"support_line": 2, "engineer_id": chosen_id, "status": "in_progress"})
        new_line = 2
        new_status = "in_progress"

    elif direction == "to_cs":
        update_data.update({"support_line": 1, "status": "waiting_cs"})
        new_line = 1
        new_status = "waiting_cs"

    else:  # to_engineers_self
        if role not in ("engineer", "director", "admin"):
            raise HTTPException(
                status_code=403, detail="Только инженер может взять тикет обратно")
        update_data.update({"support_line": 2, "status": "in_progress"})
        new_line = 2
        new_status = "in_progress"

    await TrackerTicketsDAO.update(db, filter_by={"id": ticket_id}, **update_data)
    await db.commit()

    await assign_new_line_history(
        ticket_id=ticket_id,
        user_id=user_id,
        new_line=new_line,
        assigned_engineer_id=chosen_id,
    )

    return {
        "line":          new_line,
        "status":        new_status,
        "status_label":  STATUS_DISPLAY.get(new_status, new_status),
        "assigned_to":   update_data.get("engineer_id"),
        "assigned_name": assigned_name,
    }


# ════════════════════════════════════════════════════════════════════════════
# Чат тикета из tracker_messages  (source=ks / partner / tech)
# Маршруты: /tracker/{ticket_id}/chat  +  /tracker/{ticket_id}/chat/updates
# ════════════════════════════════════════════════════════════════════════════

_TRACKER_RECEIPT_READER_SQL = """
    AND (
        (r.person_type = 'skystream' AND au.role IN ('support', 'engineer', 'director', 'admin'))
        OR (r.person_type = 'skystream' AND au.role IS NULL)
    )
"""


async def _resolve_tracker_reader_display(
    db: AsyncSession,
    user_id: int,
    person_type: str,
    viewer_role: str,
) -> tuple:
    """Имя читателя и роль для галочек прочтения (КС / инженеры)."""
    if (person_type or "skystream") != "skystream":
        name = await _resolve_author_name(db, user_id, person_type, viewer_role)
        return name, person_type
    row = (await db.execute(
        text("SELECT full_name, role FROM users.skystream_users WHERE id = :uid"),
        {"uid": user_id},
    )).mappings().first()
    if not row:
        return f"ID {user_id}", None
    role = (row.get("role") or "").lower()
    if role == "support":
        return "Контактный сервис", role
    return (row.get("full_name") or f"ID {user_id}"), role


async def _resolve_author_name(
    db: AsyncSession,
    author_id: int,
    person_type: Optional[str],
    viewer_role: str,
) -> str:
    """Возвращает отображаемое имя автора (ФИО для инженеров на странице тикета)."""
    pt = (person_type or "skystream").lower()

    if pt == "skystream":
        row = (await db.execute(
            text("SELECT full_name FROM users.skystream_users WHERE id = :uid"),
            {"uid": author_id},
        )).mappings().first()
        return (row["full_name"] or f"ID {author_id}") if row else f"ID {author_id}"

    if pt == "tech":
        row = (await db.execute(
            text("SELECT full_name FROM partner.technicians WHERE technician_id = :uid"),
            {"uid": author_id},
        )).mappings().first()
        return (row["full_name"] if row and row["full_name"] else f"Техник {author_id}")

    if pt == "partner":
        row = (await db.execute(
            text("SELECT fullname FROM partner.diler WHERE id = :uid"),
            {"uid": author_id},
        )).mappings().first()
        return (row["fullname"] if row and row["fullname"] else f"Партнёр {author_id}")

    return f"ID {author_id}"


async def _build_tracker_messages(
    db: AsyncSession,
    rows: list,
    viewer_id: int,
    viewer_role: str,
) -> list:
    """Обогащает строки tracker_messages именами авторов, прочтениями и вложениями."""
    if not rows:
        return []

    msg_ids = [r["id"] for r in rows]
    ids_placeholder = ", ".join(str(i) for i in msg_ids)

    reads_sql = text(f"""
        SELECT r.msg_id, r.user_id, r.person_type, r.read_time, au.role AS reader_role
        FROM users.tracker_messages_reads r
        LEFT JOIN users.skystream_users au ON au.id = r.user_id AND r.person_type = 'skystream'
        WHERE r.msg_id IN ({ids_placeholder})
        {_TRACKER_RECEIPT_READER_SQL}
        ORDER BY r.read_time ASC
    """)
    reads_rows = (await db.execute(reads_sql)).mappings().all()

    reads_by_msg: Dict[int, list] = {}
    for rr in reads_rows:
        reads_by_msg.setdefault(rr["msg_id"], []).append(dict(rr))

    # Вложения
    attach_sql = text(f"""
        SELECT id, msg_id, file_path, original_filename, file_ext, file_size_bytes
        FROM users.tracker_message_attachments
        WHERE msg_id IN ({ids_placeholder})
        ORDER BY id ASC
    """)
    attach_rows = (await db.execute(attach_sql)).mappings().all()
    attach_by_msg: Dict[int, list] = {}
    for ar in attach_rows:
        attach_by_msg.setdefault(ar["msg_id"], []).append({
            "id": ar["id"],
            "file_path": ar["file_path"],
            "original_filename": ar["original_filename"],
            "file_ext": ar["file_ext"],
            "file_size_bytes": ar["file_size_bytes"],
        })

    # Обогащаем имена читателей
    reader_cache: Dict[str, tuple] = {}
    for rr in reads_rows:
        cache_key = f"{rr['person_type']}:{rr['user_id']}"
        if cache_key not in reader_cache:
            reader_cache[cache_key] = await _resolve_tracker_reader_display(
                db, rr["user_id"], rr["person_type"], viewer_role
            )

    reply_to_ids = list({int(r["reply_to_id"]) for r in rows if r.get("reply_to_id")})
    reply_parents: Dict[int, dict] = {}
    if reply_to_ids:
        reply_ph = ", ".join(str(i) for i in reply_to_ids)
        reply_sql = text(f"""
            SELECT id, body, author_id, person_type
            FROM users.tracker_messages
            WHERE id IN ({reply_ph})
        """)
        for pr in (await db.execute(reply_sql)).mappings().all():
            reply_parents[int(pr["id"])] = dict(pr)

    reply_author_cache: Dict[tuple, str] = {}

    result = []
    for r in rows:
        author_name = await _resolve_author_name(
            db, r["author_id"], r.get("person_type"), viewer_role
        )
        reads = []
        for rr in reads_by_msg.get(r["id"], []):
            cache_key = f"{rr['person_type']}:{rr['user_id']}"
            display_name, reader_role = reader_cache.get(cache_key, ("—", None))
            reads.append({
                "user_id": rr["user_id"],
                "person_type": rr["person_type"],
                "display_name": display_name,
                "reader_role": reader_role or rr.get("reader_role"),
                "read_time": rr["read_time"].isoformat() if rr["read_time"] else None,
            })

        reply_to_id = r.get("reply_to_id")
        reply_to_deleted = False
        reply_to_author = None
        reply_to_snippet = None
        if reply_to_id:
            parent = reply_parents.get(int(reply_to_id))
            if parent:
                pkey = (parent["author_id"], parent.get("person_type"))
                if pkey not in reply_author_cache:
                    reply_author_cache[pkey] = await _resolve_author_name(
                        db, parent["author_id"], parent.get("person_type"), viewer_role
                    )
                reply_to_author = reply_author_cache[pkey]
                body_plain = re.sub(r"<[^>]+>", " ", parent.get("body") or "")
                reply_to_snippet = " ".join(body_plain.split())[:80] or None
            else:
                reply_to_deleted = True

        result.append({
            "id": r["id"],
            "ticket_id": r["ticket_id"],
            "author_id": r["author_id"],
            "person_type": r.get("person_type") or "skystream",
            "author_name": author_name,
            "body": r["body"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "is_edited": bool(r["is_edited"]),
            "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
            "reply_to_id": reply_to_id,
            "reply_to_deleted": reply_to_deleted,
            "reply_to_author": reply_to_author,
            "reply_to_snippet": reply_to_snippet,
            "reads": reads,
            "attachments": attach_by_msg.get(r["id"], []),
        })
    return result


@router.get("/tracker/{ticket_id}/chat")
async def get_tracker_chat(
    ticket_id: int,
    before_id: Optional[int] = Query(None),
    after_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Список сообщений из tracker_messages для тикета (чат KS/partner/tech)."""
    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")

    if before_id is not None:
        sql = text("""
            SELECT id, ticket_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE ticket_id = :tid AND id < :bid
            ORDER BY id DESC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"tid": ticket_id, "bid": before_id, "lim": limit})).mappings().all()
        rows = list(reversed(rows))
    elif after_id is not None:
        sql = text("""
            SELECT id, ticket_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE ticket_id = :tid AND id > :aid
            ORDER BY id ASC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"tid": ticket_id, "aid": after_id, "lim": limit})).mappings().all()
        rows = list(rows)
    else:
        sql = text("""
            SELECT id, ticket_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE ticket_id = :tid
            ORDER BY id DESC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"tid": ticket_id, "lim": limit})).mappings().all()
        rows = list(reversed(rows))

    return await _build_tracker_messages(db, [dict(r) for r in rows], viewer_id, viewer_role)


@router.get("/tracker/{ticket_id}/chat/updates")
async def get_tracker_chat_updates(
    ticket_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает max id сообщения для поллинга."""
    row = (await db.execute(
        text("SELECT MAX(id) AS max_id FROM users.tracker_messages WHERE ticket_id = :tid"),
        {"tid": ticket_id},
    )).mappings().first()
    return {"max_msg_id": row["max_id"] if row and row["max_id"] else 0}


@router.post("/tracker/{ticket_id}/chat/attachments/upload")
async def upload_tracker_chat_attachment(
    ticket_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Фаза A двухфазной отправки: загрузить ОДИН файл во временную папку ДО
    создания сообщения. Возвращает подписанный токен — запись в БД не делается."""
    ticket_row = (await db.execute(
        text("SELECT id FROM users.tracker_tickets WHERE id = :tid"),
        {"tid": ticket_id},
    )).fetchone()
    if not ticket_row:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    form = await request.form()
    file = form.get("file")
    if not file or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="Файл не передан")
    contents, original_filename = await read_upload_file(file)
    return save_attachment_temp(contents, original_filename, operator_id=operator.get("user_id") or 0)


@router.post("/tracker/{ticket_id}/chat", status_code=201)
async def post_tracker_chat_message(
    ticket_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение в чат тикета (tracker_messages).

    JSON c upload_tokens: сообщение + вложения создаются в ОДНОЙ транзакции
        (двухфазная отправка) — другие проекты не видят пустое сообщение.
    JSON без файлов: только текст.
    multipart: body + files[] — текст сразу в ответе, файлы пишутся в фоне (legacy).
    """
    upload_files: List[UploadFile] = []
    upload_tokens: List[str] = []
    attachments_follow = False
    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        body_text = (form.get("body") or "").strip()
        reply_to_id = _parse_optional_reply_to_id(form.get("reply_to_id"))
        upload_files = collect_upload_files_from_form(form)
    else:
        body_data = await request.json()
        body_text = (body_data.get("body") or "").strip()
        reply_to_id = _parse_optional_reply_to_id(body_data.get("reply_to_id"))
        attachments_follow = bool(body_data.get("has_attachments"))
        raw_tokens = body_data.get("upload_tokens")
        if isinstance(raw_tokens, list):
            upload_tokens = [str(t) for t in raw_tokens if t]

    if body_text == "" and not upload_files and not attachments_follow and not upload_tokens:
        raise HTTPException(status_code=422, detail="Пустое сообщение")
    if body_text == "":
        body_text = " "

    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")

    ticket_row = (await db.execute(
        text("SELECT id FROM users.tracker_tickets WHERE id = :tid"),
        {"tid": ticket_id},
    )).fetchone()
    if not ticket_row:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    insert_sql = text("""
        INSERT INTO users.tracker_messages
            (ticket_id, author_id, person_type, body, reply_to_id, created_at, is_edited)
        VALUES
            (:tid, :author, 'skystream', :body, :reply_to, now(), false)
        RETURNING id, ticket_id, author_id, person_type, body,
                  created_at, is_edited, updated_at, reply_to_id
    """)

    # ── Двухфазный путь: сообщение + вложения в одной транзакции ──────────────
    if upload_tokens:
        prepared, tmp_paths = load_upload_tokens(upload_tokens, operator_id=viewer_id)
        try:
            row = (await db.execute(insert_sql, {
                "tid": ticket_id,
                "author": viewer_id,
                "body": body_text,
                "reply_to": reply_to_id,
            })).mappings().first()
            await save_tracker_prepared_attachments(
                db, ticket_id=ticket_id, msg_id=row["id"], prepared=prepared, commit=False,
            )
            await db.commit()
        except HTTPException:
            raise
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Не удалось сохранить вложения")
        cleanup_temp_files(tmp_paths)

        participant_update = await ensure_engineer_participant_on_message(
            db, ticket_id, viewer_id, (viewer_role or "").lower()
        )
        msgs = await _build_tracker_messages(db, [dict(row)], viewer_id, viewer_role)
        out = msgs[0] if msgs else {}
        if participant_update:
            out.update(participant_update)
        return out

    # ── Legacy путь (текст / multipart с фоновой записью) ─────────────────────
    prepared_files = []
    if upload_files:
        prepared_files = await prepare_tracker_upload_files(upload_files)

    row = (await db.execute(insert_sql, {
        "tid": ticket_id,
        "author": viewer_id,
        "body": body_text,
        "reply_to": reply_to_id,
    })).mappings().first()
    await db.commit()

    if prepared_files:
        background_tasks.add_task(
            persist_tracker_attachments_background,
            ticket_id,
            row["id"],
            prepared_files,
        )

    participant_update = await ensure_engineer_participant_on_message(
        db, ticket_id, viewer_id, (viewer_role or "").lower()
    )

    msgs = await _build_tracker_messages(db, [dict(row)], viewer_id, viewer_role)
    out = msgs[0] if msgs else {}
    if prepared_files:
        out["attachments_pending"] = True
        out["attachments"] = []
    if participant_update:
        out.update(participant_update)
    return out


@router.put("/tracker/{ticket_id}/chat/{msg_id}")
async def edit_tracker_chat_message(
    ticket_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Редактировать своё сообщение в tracker_messages."""
    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")
    body_data = await request.json()
    new_body = (body_data.get("body") or "").strip()
    if not new_body:
        raise HTTPException(status_code=422, detail="Пустое сообщение")

    row = (await db.execute(
        text("""
            SELECT id, author_id, person_type FROM users.tracker_messages
            WHERE id = :mid AND ticket_id = :tid
        """),
        {"mid": msg_id, "tid": ticket_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if row["author_id"] != viewer_id or (row.get("person_type") or "skystream") != "skystream":
        raise HTTPException(
            status_code=403, detail="Нельзя редактировать чужое сообщение")

    updated = (await db.execute(
        text("""
            UPDATE users.tracker_messages
            SET body = :body, is_edited = true, updated_at = now()
            WHERE id = :mid
            RETURNING id, ticket_id, author_id, person_type, body,
                      created_at, is_edited, updated_at, reply_to_id
        """),
        {"body": new_body, "mid": msg_id},
    )).mappings().first()
    await db.commit()

    msgs = await _build_tracker_messages(db, [dict(updated)], viewer_id, viewer_role)
    return msgs[0] if msgs else {}


@router.delete("/tracker/{ticket_id}/chat/{msg_id}", status_code=204)
async def delete_tracker_chat_message(
    ticket_id: int,
    msg_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить своё сообщение из tracker_messages."""
    viewer_id = operator.get("user_id") or 0

    row = (await db.execute(
        text("""
            SELECT author_id, person_type FROM users.tracker_messages
            WHERE id = :mid AND ticket_id = :tid
        """),
        {"mid": msg_id, "tid": ticket_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if row["author_id"] != viewer_id or (row.get("person_type") or "skystream") != "skystream":
        raise HTTPException(
            status_code=403, detail="Нельзя удалить чужое сообщение")

    await db.execute(
        text("DELETE FROM users.tracker_messages WHERE id = :mid"),
        {"mid": msg_id},
    )
    await db.commit()
    return Response(status_code=204)


@router.post("/tracker/{ticket_id}/chat/read", status_code=200)
async def mark_tracker_chat_read(
    ticket_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Отметить сообщения tracker_messages как прочитанные текущим пользователем.

    Только чужие сообщения (не свои) записываются в tracker_messages_reads.
    """
    viewer_id = operator.get("user_id") or 0
    body_data = await request.json()
    message_ids: List[int] = body_data.get("message_ids") or []
    if not message_ids:
        return {"marked": 0}

    ids_placeholder = ", ".join(str(int(i)) for i in message_ids)

    # Берём только чужие сообщения (person_type != skystream ИЛИ author_id != viewer)
    rows = (await db.execute(
        text(f"""
            SELECT id FROM users.tracker_messages
            WHERE id IN ({ids_placeholder})
              AND ticket_id = :tid
              AND NOT (author_id = :uid AND COALESCE(person_type, 'skystream') = 'skystream')
        """),
        {"tid": ticket_id, "uid": viewer_id},
    )).fetchall()

    marked = 0
    for row in rows:
        try:
            await db.execute(
                text("""
                    INSERT INTO users.tracker_messages_reads (msg_id, user_id, person_type, read_time)
                    VALUES (:mid, :uid, 'skystream', now())
                    ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
                """),
                {"mid": row[0], "uid": viewer_id},
            )
            marked += 1
        except Exception:
            pass

    await db.commit()
    return {"marked": marked}


async def _fetch_tracker_messages_by_ids(
    db: AsyncSession,
    msg_ids: List[int],
    viewer_id: int,
    viewer_role: str,
    *,
    ticket_id: Optional[int] = None,
    incident_id: Optional[int] = None,
) -> list:
    """Загрузить сообщения tracker_messages по id для синхронизации чата."""
    if not msg_ids:
        return []
    ids_placeholder = ", ".join(str(int(i)) for i in msg_ids)
    if ticket_id is not None:
        scope_sql = f"ticket_id = :scope_id AND id IN ({ids_placeholder})"
    elif incident_id is not None:
        scope_sql = f"incident_id = :scope_id AND id IN ({ids_placeholder})"
    else:
        return []

    sql = text(f"""
        SELECT id, ticket_id, incident_id, author_id, person_type, body,
               created_at, is_edited, updated_at, reply_to_id
        FROM users.tracker_messages
        WHERE {scope_sql}
        ORDER BY id ASC
    """)
    rows = (await db.execute(sql, {"scope_id": ticket_id or incident_id})).mappings().all()
    return await _build_tracker_messages(db, [dict(r) for r in rows], viewer_id, viewer_role)


@router.get("/tracker/{ticket_id}/chat/sync")
async def sync_tracker_chat_messages(
    ticket_id: int,
    msg_ids: str = Query(..., description="ID сообщений через запятую"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Актуальное состояние сообщений tracker_messages для поллинга."""
    try:
        ids = [int(x.strip()) for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid msg_ids")
    if not ids:
        return {"messages": []}
    if len(ids) > 200:
        raise HTTPException(status_code=400, detail="Too many msg_ids (max 200)")

    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")
    messages = await _fetch_tracker_messages_by_ids(
        db, ids, viewer_id, viewer_role, ticket_id=ticket_id,
    )
    return {"messages": messages}


@router.get("/tracker/{ticket_id}/chat/reads")
async def get_tracker_chat_reads(
    ticket_id: int,
    msg_ids: str = Query(..., description="Список ID сообщений через запятую"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает актуальные прочтения для указанных сообщений tracker_messages.

    Используется поллингом, чтобы обновлять галочки «прочитано» без перезагрузки.
    """
    viewer_role = operator.get("role", "engineer")

    try:
        ids = [int(x.strip())
               for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        return {}
    if not ids:
        return {}

    ids_placeholder = ", ".join(str(i) for i in ids)
    reads_sql = text(f"""
        SELECT r.msg_id, r.user_id, r.person_type, r.read_time, au.role AS reader_role
        FROM users.tracker_messages_reads r
        LEFT JOIN users.skystream_users au ON au.id = r.user_id AND r.person_type = 'skystream'
        WHERE r.msg_id IN ({ids_placeholder})
        {_TRACKER_RECEIPT_READER_SQL}
        ORDER BY r.read_time ASC
    """)
    reads_rows = (await db.execute(reads_sql)).mappings().all()

    reader_cache: Dict[str, tuple] = {}
    for rr in reads_rows:
        cache_key = f"{rr['person_type']}:{rr['user_id']}"
        if cache_key not in reader_cache:
            reader_cache[cache_key] = await _resolve_tracker_reader_display(
                db, rr["user_id"], rr["person_type"], viewer_role
            )

    result: Dict[int, list] = {i: [] for i in ids}
    for rr in reads_rows:
        cache_key = f"{rr['person_type']}:{rr['user_id']}"
        display_name, reader_role = reader_cache.get(cache_key, ("—", None))
        result[rr["msg_id"]].append({
            "user_id": rr["user_id"],
            "person_type": rr["person_type"],
            "display_name": display_name,
            "reader_role": reader_role or rr.get("reader_role"),
            "read_time": rr["read_time"].isoformat() if rr["read_time"] else None,
        })

    return result


# ───────────────────────────────────────────────
# GET /tracker/{ticket_id}/chat/attachments/{attachment_id}/download
# ───────────────────────────────────────────────
@router.get("/tracker/{ticket_id}/chat/attachments/{attachment_id}/download")
async def download_tracker_chat_attachment(
    ticket_id: int,
    attachment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Скачать вложение по id (без кириллицы в URL — надёжнее, чем прямой /media/…)."""
    disk, filename, media_type = await resolve_tracker_attachment_download(
        db, attachment_id=attachment_id, ticket_id=ticket_id,
    )
    return tracker_attachment_file_response(disk, filename, media_type)


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/chat/{msg_id}/attachments/batch — все вложения разом
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/chat/{msg_id}/attachments/batch", status_code=201)
async def upload_tracker_attachments_batch(
    ticket_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить несколько вложений к сообщению в одной транзакции (всё или ничего)."""
    form = await request.form()
    files = collect_upload_files_from_form(form)
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не переданы")
    records = await save_tracker_message_attachments(
        db, ticket_id=ticket_id, msg_id=msg_id, files=files,
    )
    return {"attachments": records}


# ───────────────────────────────────────────────
# POST /tracker/{ticket_id}/chat/{msg_id}/attachments — загрузить вложение
# ───────────────────────────────────────────────
@router.post("/tracker/{ticket_id}/chat/{msg_id}/attachments", status_code=201)
async def upload_tracker_attachment(
    ticket_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить один файл-вложение к сообщению tracker_messages. Лимит 15 МБ."""
    form = await request.form()
    file: UploadFile = form.get("file")
    if not file or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="Файл не передан")
    records = await save_tracker_message_attachments(
        db, ticket_id=ticket_id, msg_id=msg_id, files=[file],
    )
    return records[0] if records else {}


# ───────────────────────────────────────────────
# DELETE /tracker/{ticket_id}/chat/{msg_id}/attachments/{attachment_id}
# ───────────────────────────────────────────────
@router.delete("/tracker/{ticket_id}/chat/{msg_id}/attachments/{attachment_id}")
async def delete_tracker_attachment(
    ticket_id: int,
    msg_id: int,
    attachment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить вложение из сообщения tracker_messages."""
    rec = (await db.execute(
        text("""
            SELECT a.id, a.file_path
            FROM users.tracker_message_attachments a
            JOIN users.tracker_messages m ON m.id = a.msg_id
            WHERE a.id = :aid AND a.msg_id = :mid AND m.ticket_id = :tid
        """),
        {"aid": attachment_id, "mid": msg_id, "tid": ticket_id},
    )).fetchone()
    if not rec:
        raise HTTPException(status_code=404, detail="Вложение не найдено")

    disk = disk_path_from_media_url(rec[1] or "")
    if disk and os.path.isfile(disk):
        try:
            os.unlink(disk)
        except OSError:
            logger.warning(
                "delete_tracker_attachment: не удалось удалить %s", disk)

    await db.execute(
        text("DELETE FROM users.tracker_message_attachments WHERE id = :aid"),
        {"aid": attachment_id},
    )
    await db.commit()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# INCIDENTS — эндпоинты для инцидентов из monitoring.incidents
# Чат: users.tracker_messages (incident_id), внутренние комментарии: monitoring.incident_comments
# ═══════════════════════════════════════════════════════════════════════════════


# ── GET /incidents/{id} — данные инцидента ─────────────────────────────────

@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Краткие данные инцидента для поллинга и обновлений."""
    row = (await db.execute(
        text("""
            SELECT id, status, assigned_engineer_id, type AS incident_type
            FROM monitoring.incidents WHERE id = :iid
        """),
        {"iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Инцидент не найден")
    status_raw_db = (row["status"] or "NEW").upper()
    status_raw = _INCIDENT_STATUS_MAP.get(status_raw_db, "pending")
    return {
        "id": incident_id,
        "status": status_raw,
        "status_db": status_raw_db,
        "status_label": _INCIDENT_STATUS_DISPLAY.get(status_raw_db, status_raw),
        "is_open": status_raw_db in _INCIDENT_OPEN_STATUSES,
        "assigned_to": row["assigned_engineer_id"],
        "incident_type": row["incident_type"],
    }


# ── GET /incidents/{id}/poll — поллинг статуса ─────────────────────────────
@router.get("/incidents/{incident_id}/poll")
async def poll_incident_updates(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Лёгкий эндпоинт для поллинга: статус инцидента + max_msg_id чата."""
    cache_key = f"poll:incident:{incident_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return Response(content=cached, media_type="application/json")

    row = (await db.execute(
        text("SELECT status FROM monitoring.incidents WHERE id = :iid"),
        {"iid": incident_id},
    )).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    status_raw_db = (row[0] or "NEW").upper()
    status_raw = _INCIDENT_STATUS_MAP.get(status_raw_db, "pending")

    max_id_row = (await db.execute(
        text("SELECT COALESCE(MAX(id), 0) FROM users.tracker_messages WHERE incident_id = :iid"),
        {"iid": incident_id},
    )).scalar()

    result = {
        "status": status_raw,
        "status_label": _INCIDENT_STATUS_DISPLAY.get(status_raw_db, status_raw),
        "max_msg_id": int(max_id_row or 0),
        "is_open": status_raw_db in _INCIDENT_OPEN_STATUSES,
    }
    payload = json.dumps(result, ensure_ascii=False)
    try:
        await redis_client.setex(cache_key, 5, payload)
    except Exception:
        pass
    return Response(content=payload, media_type="application/json")


# ── PATCH /incidents/{id}/status — смена статуса ──────────────────────────
@router.patch("/incidents/{incident_id}/status")
async def change_incident_status(
    incident_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Изменяет статус инцидента. Принимает display-статус (in_progress, deferred, resolved, not_resolved)."""
    body_data = await request.json()
    status_display = (body_data.get("status") or "").strip()
    # Поддерживаем также прямую передачу DB-статуса
    status_db = INCIDENT_STATUS_TO_DB.get(status_display) or (
        status_display.upper() if status_display.upper() in _INCIDENT_OPEN_STATUSES | {
            "RESOLVED_MANUAL", "RESOLVED_AUTO", "UNRESOLVED"} else None
    )
    if not status_db:
        raise HTTPException(
            status_code=422, detail=f"Неизвестный статус: {status_display}")

    row = (await db.execute(
        text("SELECT id, assigned_engineer_id, resolved_at FROM monitoring.incidents WHERE id = :iid"),
        {"iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    now = datetime.now(timezone.utc)
    if status_db in ("NEW", "IN_PROGRESS", "POSTPONED"):
        resolved_at = row.get("resolved_at")
        if resolved_at:
            if getattr(resolved_at, "tzinfo", None) is None:
                resolved_at = resolved_at.replace(tzinfo=timezone.utc)
            if (now - resolved_at).days >= 7:
                raise HTTPException(
                    status_code=403,
                    detail="Нельзя переоткрыть инцидент старше 7 дней",
                )

    params: Dict[str, Any] = {"iid": incident_id}
    extra_set = ""
    if status_db in ("RESOLVED_MANUAL", "RESOLVED_AUTO", "UNRESOLVED"):
        extra_set = ", resolved_at = :resolved_at, closing_engineer_id = :closing_eng"
        params["resolved_at"] = now
        params["closing_eng"] = operator.get("user_id")
    elif status_db in ("NEW", "IN_PROGRESS", "POSTPONED"):
        extra_set = ", resolved_at = NULL, closing_engineer_id = NULL"
    if status_db == "IN_PROGRESS" and not row["assigned_engineer_id"]:
        extra_set += ", assigned_engineer_id = :eng_id"
        params["eng_id"] = operator.get("user_id")

    await db.execute(
        text(
            f"UPDATE monitoring.incidents SET status = '{status_db}'::monitoring.issue_status {extra_set} WHERE id = :iid"),
        params,
    )
    await db.commit()

    try:
        await redis_client.delete(f"poll:incident:{incident_id}")
    except Exception:
        pass

    status_raw = _INCIDENT_STATUS_MAP.get(status_db, "pending")
    return {
        "status": status_raw,
        "status_db": status_db,
        "status_label": _INCIDENT_STATUS_DISPLAY.get(status_db, status_raw),
        "is_open": status_db in _INCIDENT_OPEN_STATUSES,
    }


# ── GET /incidents/{id}/station-info — метрики станции (type=STATION) ──────
@router.get("/incidents/{incident_id}/station-info")
async def get_incident_station_info(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
    db_zabbix: Optional[AsyncSession] = Depends(get_db_zabbix_optional),
):
    """Информация по станции для инцидента type=STATION (user_id = station_id)."""
    row = (await db.execute(
        text("SELECT type, user_id FROM monitoring.incidents WHERE id = :iid"),
        {"iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    station_id = row["user_id"]
    if not station_id:
        return {"station_id": None, "station_name": None, "is_online": False}

    station_name = await StationFormsDAO.get_station_name(session=db, station_id=station_id)
    if not station_name:
        station_name = f"Станция #{station_id}"

    station_group = await IpGroupDAO.find_one_or_none(session=db, id=station_id)
    if not station_group:
        return {"station_id": station_id, "station_name": station_name, "is_online": False,
                "last_online": None, "vno_name": None, "metrics": {}, "equipment": {}, "address": None,
                "master": None, "master_phone": None, "partner_id": None}

    aliveness = await AlivenessStatusDAO.find_one_or_none(session=db, station_id=station_id)
    is_online = bool(aliveness.get("is_alive")) if aliveness else False
    last_online = aliveness.get("updated_at").isoformat(
    ) if aliveness and aliveness.get("updated_at") else None

    vno_name = None
    vno_id = station_group.get("vno")
    if vno_id:
        vno_row = await VirtualNetworkOperatorDAO.find_one_or_none(session=db, id=vno_id)
        vno_name = (vno_row.get("name") or "—") if vno_row else "—"

    ig = dict(station_group)
    parts = [ig.get("city"), ig.get("district"),
             ig.get("street"), ig.get("house")]
    address = ", ".join(p for p in parts if p) or None
    partner_id = ig.get("id_diler")

    sf = await StationFormsDAO.find_one_or_none(session=db, station_id=station_id)
    equipment: Dict[str, Any] = {}
    master = None
    master_phone = None
    if sf:
        if sf.get("antenna_diameter") is not None:
            equipment["antenna_diameter"] = sf["antenna_diameter"]
        if sf.get("buc_power") is not None:
            equipment["buc_power"] = sf["buc_power"]
        if sf.get("modem_model"):
            equipment["modem_model"] = sf["modem_model"]
        elif sf.get("modem_brand"):
            equipment["modem_model"] = sf["modem_brand"]
        if sf.get("router_brand"):
            equipment["router_brand"] = sf["router_brand"]
        if sf.get("station_address"):
            address = sf["station_address"]
        master = sf.get("station_master") or None
        master_phone = sf.get("station_master_phone") or None
    if station_group.get("modem"):
        equipment["modem_ip"] = str(station_group["modem"])
    if station_group.get("router_ip"):
        equipment["router_ip"] = str(station_group["router_ip"])
    if station_group.get("network_hotspot"):
        equipment["network_hotspot"] = str(station_group["network_hotspot"])
    if station_group.get("network_pppoe"):
        equipment["network_pppoe"] = str(station_group["network_pppoe"])

    metrics: Dict[str, Any] = {}
    try:
        users_info = await get_users_short_info(db, operator, station_id)
        metrics["subscribers_total"] = users_info.get("total", 0)
        metrics["subscribers_with_tariff"] = users_info.get("with_tariff", 0)
        metrics["subscribers_online"] = users_info.get("online", 0)
    except Exception:
        pass

    yearmonth = get_yesterday_ym()
    stats = await MonthlyStationStatsDAO.find_one_or_none(session=db, station_id=station_id, yearmonth=yearmonth)
    channel_id = station_group.get("channel_id")
    antenna_size = (sf.get("antenna_diameter")
                    if sf else None) or station_group.get("antenna_cm_")
    thresholds: List[Dict[str, Any]] = []
    if channel_id and antenna_size is not None:
        try:
            ant_int = int(antenna_size)
            thresholds = await SatelliteThresholdsDAO.find_all(session=db, satellite=channel_id, antenna_size=ant_int) or []
        except (TypeError, ValueError):
            pass
    if stats:
        def _f(v):
            return round(float(v), 2) if v is not None else None
        avg_signal = _f(stats.get("avg_signal"))
        avg_signal_1d = _f(stats.get("avg_signal_1d"))
        avg_signal_7d = _f(stats.get("avg_signal_7d"))
        avg_bit_hz = _f(stats.get("avg_bit_hz"))
        avg_bit_hz_1d = _f(stats.get("avg_bit_hz_1d"))
        avg_bit_hz_7d = _f(stats.get("avg_bit_hz_7d"))
        metrics["signal_level"] = avg_signal
        metrics["signal_avg_1d"] = avg_signal_1d
        metrics["signal_avg_7d"] = avg_signal_7d
        metrics["signal_status"] = define_signal_and_bytegz_status(
            thresholds, "signal", avg_signal)
        metrics["bit_per_hz"] = avg_bit_hz
        metrics["bit_per_hz_1d"] = avg_bit_hz_1d
        metrics["bit_per_hz_7d"] = avg_bit_hz_7d
        metrics["bit_per_hz_status"] = define_signal_and_bytegz_status(
            thresholds, "bit_per_hz", avg_bit_hz)
    if db_zabbix and (not stats or metrics.get("signal_level") is None):
        try:
            zabbix = await get_last_hour_metrics(db, db_zabbix, operator, station_group)
            if zabbix.get("has_signal") and zabbix.get("avg_signal") is not None:
                metrics["signal_level"] = round(float(zabbix["avg_signal"]), 1)
            if zabbix.get("has_bytegz") and zabbix.get("avg_bytegz") is not None:
                metrics["bit_per_hz"] = zabbix["avg_bytegz"]
        except Exception:
            pass

    return {
        "station_id": station_id,
        "station_name": station_name,
        "is_online": is_online,
        "last_online": last_online,
        "vno_name": vno_name,
        "metrics": metrics,
        "equipment": equipment,
        "address": address,
        "master": master,
        "master_phone": master_phone,
        "partner_id": partner_id,
    }


# ── GET /incidents/{id}/partner-info — информация о партнёре ───────────────
@router.get("/incidents/{incident_id}/partner-info")
async def get_incident_partner_info(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Партнёр инцидента и доступные техники для привязки.

    Для type=USER: user_id → users.user.id_grp → wifitochka.ip_group.id_diler.
    Для type=STATION: user_id (= station_id) → wifitochka.ip_group.id_diler.
    """
    row = (await db.execute(
        text("SELECT user_id, type FROM monitoring.incidents WHERE id = :iid"),
        {"iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    entity_id = row["user_id"]
    incident_type = (row["type"] or "USER").upper()

    station_id = None
    if incident_type == "USER":
        id_grp_row = (await db.execute(
            text("SELECT id_grp FROM users.user WHERE id = :uid"),
            {"uid": entity_id},
        )).mappings().first()
        station_id = id_grp_row["id_grp"] if id_grp_row else None
    else:
        station_id = entity_id

    if not station_id:
        return {"partner_id": None, "partner_name": None, "technicians": []}

    ip_group_row = (await db.execute(
        text("SELECT id_diler FROM wifitochka.ip_group WHERE id = :sid"),
        {"sid": station_id},
    )).mappings().first()
    partner_id = ip_group_row["id_diler"] if ip_group_row else None

    if not partner_id:
        return {"partner_id": None, "partner_name": None, "technicians": []}

    partner_row = (await db.execute(
        text("SELECT fullname FROM partner.diler WHERE id = :pid"),
        {"pid": partner_id},
    )).mappings().first()
    partner_name = (partner_row["fullname"] or "").strip(
    ) if partner_row else f"Партнёр #{partner_id}"

    tech_rows = (await db.execute(
        text("""
            SELECT t.technician_id AS id, t.full_name
            FROM partner.technicians t
            INNER JOIN partner.technicians_partners tp
                ON tp.technician_id = t.technician_id AND tp.partner_id = :pid
            ORDER BY t.full_name NULLS LAST, t.technician_id
        """),
        {"pid": partner_id},
    )).mappings().all()
    technicians = [
        {"id": r["id"], "full_name": (
            r["full_name"] or "").strip() or f"Техник {r['id']}"}
        for r in tech_rows
    ]

    return {"partner_id": partner_id, "partner_name": partner_name, "technicians": technicians}


# ── GET /incidents/{id}/assignments — список назначений ────────────────────
@router.get("/incidents/{incident_id}/assignments")
async def get_incident_assignments(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Текущие назначения (партнёры и техники) для инцидента."""
    rows = (await db.execute(
        text("""
            SELECT ia.id, ia.entity_type, ia.entity_id,
                   TO_CHAR(ia.created_at, 'DD.MM.YYYY HH24:MI') AS added_at,
                   t.full_name AS tech_name
            FROM monitoring.incident_assignments ia
            LEFT JOIN partner.technicians t
                ON t.technician_id = ia.entity_id AND ia.entity_type = 'technician'
            WHERE ia.incident_id = :iid
            ORDER BY ia.created_at
        """),
        {"iid": incident_id},
    )).mappings().all()
    return [
        {
            "id": r["id"],
            "entity_type": r["entity_type"],
            "entity_id": r["entity_id"],
            "full_name": (r.get("tech_name") or "").strip() or f"ID {r['entity_id']}",
            "added_at": r.get("added_at"),
        }
        for r in rows
    ]


# ── POST /incidents/{id}/assignments — добавить назначение ─────────────────
@router.post("/incidents/{incident_id}/assignments", status_code=201)
async def add_incident_assignment(
    incident_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Добавить партнёра или техника к инциденту."""
    body = await request.json()
    entity_type = (body.get("entity_type") or "").strip()
    entity_id = body.get("entity_id")
    if entity_type not in ("partner", "technician") or not entity_id:
        raise HTTPException(
            status_code=422, detail="entity_type и entity_id обязательны")

    if not (await db.execute(
        text("SELECT 1 FROM monitoring.incidents WHERE id = :iid"), {
            "iid": incident_id}
    )).fetchone():
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    try:
        rec = (await db.execute(
            text("""
                INSERT INTO monitoring.incident_assignments
                    (incident_id, entity_type, entity_id, created_by)
                VALUES (:iid, :etype, :eid, :cby)
                RETURNING id, TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI') AS added_at
            """),
            {"iid": incident_id, "etype": entity_type, "eid": entity_id,
             "cby": operator.get("user_id")},
        )).mappings().first()
        await db.commit()
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409, detail="Назначение уже существует")
        raise HTTPException(status_code=400, detail=str(e))

    full_name = None
    if entity_type == "technician":
        t_row = (await db.execute(
            text("SELECT full_name FROM partner.technicians WHERE technician_id = :tid"),
            {"tid": entity_id},
        )).mappings().first()
        full_name = (t_row["full_name"] or "").strip() if t_row else None

    return {
        "id": rec["id"],
        "entity_type": entity_type,
        "entity_id": entity_id,
        "full_name": full_name or f"ID {entity_id}",
        "added_at": rec["added_at"],
    }


# ── DELETE /incidents/{id}/assignments/{assignment_id} ─────────────────────
@router.delete("/incidents/{incident_id}/assignments/{assignment_id}", status_code=204)
async def remove_incident_assignment(
    incident_id: int,
    assignment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить назначение из инцидента."""
    deleted = (await db.execute(
        text("DELETE FROM monitoring.incident_assignments WHERE id = :aid AND incident_id = :iid RETURNING id"),
        {"aid": assignment_id, "iid": incident_id},
    )).fetchone()
    if not deleted:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    await db.commit()
    return Response(status_code=204)


# ── GET /incidents/{id}/chat — сообщения чата инцидента ───────────────────
@router.get("/incidents/{incident_id}/chat")
async def get_incident_chat(
    incident_id: int,
    before_id: Optional[int] = Query(None),
    after_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Сообщения чата инцидента из tracker_messages (incident_id)."""
    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")

    if before_id is not None:
        sql = text("""
            SELECT id, incident_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE incident_id = :iid AND id < :bid
            ORDER BY id DESC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"iid": incident_id, "bid": before_id, "lim": limit})).mappings().all()
        rows = list(reversed(rows))
    elif after_id is not None:
        sql = text("""
            SELECT id, incident_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE incident_id = :iid AND id > :aid
            ORDER BY id ASC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"iid": incident_id, "aid": after_id, "lim": limit})).mappings().all()
        rows = list(rows)
    else:
        sql = text("""
            SELECT id, incident_id, author_id, person_type, body,
                   created_at, is_edited, updated_at, reply_to_id
            FROM users.tracker_messages
            WHERE incident_id = :iid
            ORDER BY id DESC LIMIT :lim
        """)
        rows = (await db.execute(sql, {"iid": incident_id, "lim": limit})).mappings().all()
        rows = list(reversed(rows))

    # Адаптируем строки для _build_tracker_messages: ticket_id = incident_id
    adapted = [dict(r, ticket_id=r.get("incident_id")) for r in rows]
    return await _build_tracker_messages(db, adapted, viewer_id, viewer_role)


# ── GET /incidents/{id}/chat/updates ─────────────────────────────────────
@router.get("/incidents/{incident_id}/chat/updates")
async def get_incident_chat_updates(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Max id сообщения чата инцидента для поллинга."""
    row = (await db.execute(
        text("SELECT MAX(id) AS max_id FROM users.tracker_messages WHERE incident_id = :iid"),
        {"iid": incident_id},
    )).mappings().first()
    return {"max_msg_id": row["max_id"] if row and row["max_id"] else 0}


@router.get("/incidents/{incident_id}/chat/sync")
async def sync_incident_chat_messages(
    incident_id: int,
    msg_ids: str = Query(..., description="ID сообщений через запятую"),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Актуальное состояние сообщений чата инцидента для поллинга."""
    try:
        ids = [int(x.strip()) for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid msg_ids")
    if not ids:
        return {"messages": []}
    if len(ids) > 200:
        raise HTTPException(status_code=400, detail="Too many msg_ids (max 200)")

    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")
    messages = await _fetch_tracker_messages_by_ids(
        db, ids, viewer_id, viewer_role, incident_id=incident_id,
    )
    return {"messages": messages}


# ── POST /incidents/{id}/chat — отправить сообщение ───────────────────────
@router.post("/incidents/{incident_id}/chat", status_code=201)
async def post_incident_chat_message(
    incident_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение в чат инцидента (tracker_messages.incident_id)."""
    body_data = await request.json()
    body_text = (body_data.get("body") or "").strip() or " "
    reply_to_id = _parse_optional_reply_to_id(body_data.get("reply_to_id"))
    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")

    if not (await db.execute(
        text("SELECT 1 FROM monitoring.incidents WHERE id = :iid"), {
            "iid": incident_id}
    )).fetchone():
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    row = (await db.execute(
        text("""
            INSERT INTO users.tracker_messages
                (incident_id, author_id, person_type, body, reply_to_id, created_at, is_edited)
            VALUES (:iid, :author, 'skystream', :body, :reply_to, now(), false)
            RETURNING id, incident_id, author_id, person_type, body,
                      created_at, is_edited, updated_at, reply_to_id
        """),
        {"iid": incident_id, "author": viewer_id,
            "body": body_text, "reply_to": reply_to_id},
    )).mappings().first()
    await db.commit()

    adapted = [dict(row, ticket_id=row.get("incident_id"))]
    msgs = await _build_tracker_messages(db, adapted, viewer_id, viewer_role)
    return msgs[0] if msgs else {}


# ── PUT /incidents/{id}/chat/{msg_id} — редактировать сообщение ───────────
@router.put("/incidents/{incident_id}/chat/{msg_id}")
async def edit_incident_chat_message(
    incident_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Редактировать своё сообщение в чате инцидента."""
    viewer_id = operator.get("user_id") or 0
    viewer_role = operator.get("role", "engineer")
    body_data = await request.json()
    new_body = (body_data.get("body") or "").strip()
    if not new_body:
        raise HTTPException(status_code=422, detail="Пустое сообщение")

    msg_row = (await db.execute(
        text("SELECT id, author_id, person_type FROM users.tracker_messages WHERE id = :mid AND incident_id = :iid"),
        {"mid": msg_id, "iid": incident_id},
    )).mappings().first()
    if not msg_row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if msg_row["author_id"] != viewer_id or (msg_row.get("person_type") or "skystream") != "skystream":
        raise HTTPException(
            status_code=403, detail="Нельзя редактировать чужое сообщение")

    updated = (await db.execute(
        text("""
            UPDATE users.tracker_messages
            SET body = :body, is_edited = true, updated_at = now()
            WHERE id = :mid
            RETURNING id, incident_id, author_id, person_type, body,
                      created_at, is_edited, updated_at, reply_to_id
        """),
        {"body": new_body, "mid": msg_id},
    )).mappings().first()
    await db.commit()

    adapted = [dict(updated, ticket_id=updated.get("incident_id"))]
    msgs = await _build_tracker_messages(db, adapted, viewer_id, viewer_role)
    return msgs[0] if msgs else {}


# ── DELETE /incidents/{id}/chat/{msg_id} ──────────────────────────────────
@router.delete("/incidents/{incident_id}/chat/{msg_id}", status_code=204)
async def delete_incident_chat_message(
    incident_id: int,
    msg_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить своё сообщение из чата инцидента."""
    viewer_id = operator.get("user_id") or 0
    msg_row = (await db.execute(
        text("SELECT author_id, person_type FROM users.tracker_messages WHERE id = :mid AND incident_id = :iid"),
        {"mid": msg_id, "iid": incident_id},
    )).mappings().first()
    if not msg_row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if msg_row["author_id"] != viewer_id or (msg_row.get("person_type") or "skystream") != "skystream":
        raise HTTPException(
            status_code=403, detail="Нельзя удалить чужое сообщение")
    await db.execute(
        text("DELETE FROM users.tracker_messages WHERE id = :mid"),
        {"mid": msg_id},
    )
    await db.commit()
    return Response(status_code=204)


# ── POST /incidents/{id}/chat/read ────────────────────────────────────────
@router.post("/incidents/{incident_id}/chat/read", status_code=200)
async def mark_incident_chat_read(
    incident_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Отметить сообщения инцидента как прочитанные."""
    viewer_id = operator.get("user_id") or 0
    body_data = await request.json()
    message_ids: List[int] = body_data.get("message_ids") or []
    if not message_ids:
        return {"marked": 0}

    ids_placeholder = ", ".join(str(int(i)) for i in message_ids)
    rows = (await db.execute(
        text(f"""
            SELECT id FROM users.tracker_messages
            WHERE id IN ({ids_placeholder})
              AND incident_id = :iid
              AND NOT (author_id = :uid AND COALESCE(person_type, 'skystream') = 'skystream')
        """),
        {"iid": incident_id, "uid": viewer_id},
    )).fetchall()

    marked = 0
    for row in rows:
        try:
            await db.execute(
                text("""
                    INSERT INTO users.tracker_messages_reads (msg_id, user_id, person_type, read_time)
                    VALUES (:mid, :uid, 'skystream', now())
                    ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
                """),
                {"mid": row[0], "uid": viewer_id},
            )
            marked += 1
        except Exception:
            pass
    await db.commit()
    return {"marked": marked}


# ── GET /incidents/{id}/chat/reads ────────────────────────────────────────
@router.get("/incidents/{incident_id}/chat/reads")
async def get_incident_chat_reads(
    incident_id: int,
    msg_ids: str = Query(...),
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Прочтения сообщений чата инцидента."""
    viewer_role = operator.get("role", "engineer")
    try:
        ids = [int(x.strip())
               for x in msg_ids.split(",") if x.strip().isdigit()]
    except Exception:
        return {}
    if not ids:
        return {}
    ids_placeholder = ", ".join(str(i) for i in ids)
    reads_rows = (await db.execute(
        text(f"""
            SELECT r.msg_id, r.user_id, r.person_type, r.read_time, au.role AS reader_role
            FROM users.tracker_messages_reads r
            LEFT JOIN users.skystream_users au ON au.id = r.user_id AND r.person_type = 'skystream'
            WHERE r.msg_id IN ({ids_placeholder})
            {_TRACKER_RECEIPT_READER_SQL}
            ORDER BY r.read_time ASC
        """),
    )).mappings().all()

    reader_cache: Dict[str, tuple] = {}
    for rr in reads_rows:
        ck = f"{rr['person_type']}:{rr['user_id']}"
        if ck not in reader_cache:
            reader_cache[ck] = await _resolve_tracker_reader_display(
                db, rr["user_id"], rr["person_type"], viewer_role
            )

    result: Dict[int, list] = {i: [] for i in ids}
    for rr in reads_rows:
        ck = f"{rr['person_type']}:{rr['user_id']}"
        display_name, reader_role = reader_cache.get(ck, ("—", None))
        result[rr["msg_id"]].append({
            "user_id": rr["user_id"],
            "person_type": rr["person_type"],
            "display_name": display_name,
            "reader_role": reader_role or rr.get("reader_role"),
            "read_time": rr["read_time"].isoformat() if rr["read_time"] else None,
        })
    return result


# ── POST /incidents/{id}/chat/{msg_id}/attachments ─────────────────────────
@router.post("/incidents/{incident_id}/chat/{msg_id}/attachments", status_code=201)
async def upload_incident_attachment(
    incident_id: int,
    msg_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить вложение к сообщению чата инцидента."""
    form = await request.form()
    file: UploadFile = form.get("file")
    if not file or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="Файл не передан")

    row = (await db.execute(
        text("SELECT id FROM users.tracker_messages WHERE id = :mid AND incident_id = :iid"),
        {"mid": msg_id, "iid": incident_id},
    )).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")

    contents, original_filename = await read_upload_file(file)
    ext = (Path(original_filename).suffix or "").lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")
    if not _check_file_magic(contents, ext):
        raise HTTPException(
            status_code=400, detail="Содержимое не соответствует типу файла")

    storage_user_id, storage_scope_id = await resolve_tracker_storage_scope(
        db, incident_id=incident_id,
    )
    file_path, file_ext, file_size = persist_chat_file_bytes(
        contents,
        original_filename,
        storage_user_id=storage_user_id,
        storage_scope_id=storage_scope_id,
    )

    rec = (await db.execute(
        text("""
            INSERT INTO users.tracker_message_attachments
                (msg_id, file_path, original_filename, file_ext, file_size_bytes)
            VALUES (:mid, :fp, :fn, :ext, :sz)
            RETURNING id, msg_id, file_path, original_filename, file_ext, file_size_bytes
        """),
        {"mid": msg_id, "fp": file_path, "fn": original_filename,
            "ext": file_ext or None, "sz": file_size},
    )).mappings().first()
    await db.commit()
    return dict(rec)


# ── GET /incidents/{id}/chat/attachments/{attachment_id}/download ────────────
@router.get("/incidents/{incident_id}/chat/attachments/{attachment_id}/download")
async def download_incident_chat_attachment(
    incident_id: int,
    attachment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Скачать вложение чата инцидента по id."""
    disk, filename, media_type = await resolve_tracker_attachment_download(
        db, attachment_id=attachment_id, incident_id=incident_id,
    )
    return tracker_attachment_file_response(disk, filename, media_type)


# ── DELETE /incidents/{id}/chat/{msg_id}/attachments/{att_id} ──────────────
@router.delete("/incidents/{incident_id}/chat/{msg_id}/attachments/{attachment_id}")
async def delete_incident_attachment(
    incident_id: int,
    msg_id: int,
    attachment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить вложение из сообщения чата инцидента."""
    rec = (await db.execute(
        text("""
            SELECT a.id, a.file_path
            FROM users.tracker_message_attachments a
            JOIN users.tracker_messages m ON m.id = a.msg_id
            WHERE a.id = :aid AND a.msg_id = :mid AND m.incident_id = :iid
        """),
        {"aid": attachment_id, "mid": msg_id, "iid": incident_id},
    )).fetchone()
    if not rec:
        raise HTTPException(status_code=404, detail="Вложение не найдено")

    disk = disk_path_from_media_url(rec[1] or "")
    if disk and os.path.isfile(disk):
        try:
            os.unlink(disk)
        except OSError:
            pass

    await db.execute(
        text("DELETE FROM users.tracker_message_attachments WHERE id = :aid"),
        {"aid": attachment_id},
    )
    await db.commit()
    return {"status": "deleted"}


# ── GET /incidents/{id}/comments — внутренние комментарии ──────────────────
@router.get("/incidents/{incident_id}/comments")
async def get_incident_comments(
    incident_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Список внутренних комментариев инцидента (monitoring.incident_comments)."""
    rows = (await db.execute(
        text("""
            SELECT ic.id, ic.author_id, ic.comment_text AS text,
                   TO_CHAR(ic.created_at, 'DD.MM.YYYY HH24:MI') AS created_at,
                   au.full_name AS author_name
            FROM monitoring.incident_comments ic
            LEFT JOIN users.skystream_users au ON au.id = ic.author_id
            WHERE ic.incident_id = :iid
            ORDER BY ic.created_at ASC
        """),
        {"iid": incident_id},
    )).mappings().all()
    return [dict(r) for r in rows]


# ── POST /incidents/{id}/comments ─────────────────────────────────────────
@router.post("/incidents/{incident_id}/comments", status_code=201)
async def add_incident_comment(
    incident_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Добавить внутренний комментарий к инциденту."""
    body_data = await request.json()
    text_val = (body_data.get("text") or "").strip()
    if not text_val:
        raise HTTPException(
            status_code=422, detail="Текст комментария не может быть пустым")

    author_id = operator.get("user_id")
    rec = (await db.execute(
        text("""
            INSERT INTO monitoring.incident_comments (incident_id, author_id, comment_text)
            VALUES (:iid, :author, :txt)
            RETURNING id, author_id, comment_text AS text,
                      TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI') AS created_at
        """),
        {"iid": incident_id, "author": author_id, "txt": text_val},
    )).mappings().first()
    await db.commit()

    au_row = (await db.execute(
        text("SELECT full_name FROM users.skystream_users WHERE id = :uid"), {
            "uid": author_id}
    )).mappings().first()
    author_name = (au_row["full_name"] or "").strip() if au_row else ""

    return dict(rec, author_id=author_id, author_name=author_name)


# ── PATCH /incidents/{id}/comments/{comment_id} ───────────────────────────
@router.patch("/incidents/{incident_id}/comments/{comment_id}")
async def edit_incident_comment(
    incident_id: int,
    comment_id: int,
    request: Request,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Редактировать свой внутренний комментарий инцидента."""
    viewer_id = operator.get("user_id")
    body_data = await request.json()
    text_val = (body_data.get("text") or "").strip()
    if not text_val:
        raise HTTPException(
            status_code=422, detail="Текст не может быть пустым")

    row = (await db.execute(
        text("SELECT author_id FROM monitoring.incident_comments WHERE id = :cid AND incident_id = :iid"),
        {"cid": comment_id, "iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    if row["author_id"] != viewer_id:
        raise HTTPException(
            status_code=403, detail="Нельзя редактировать чужой комментарий")

    await db.execute(
        text("UPDATE monitoring.incident_comments SET comment_text = :txt WHERE id = :cid"),
        {"txt": text_val, "cid": comment_id},
    )
    await db.commit()
    return {"id": comment_id, "text": text_val}


# ── DELETE /incidents/{id}/comments/{comment_id} ──────────────────────────
@router.delete("/incidents/{incident_id}/comments/{comment_id}", status_code=204)
async def delete_incident_comment(
    incident_id: int,
    comment_id: int,
    operator: Dict = Depends(allow_support),
    db: AsyncSession = Depends(get_db),
):
    """Удалить свой внутренний комментарий инцидента."""
    viewer_id = operator.get("user_id")
    row = (await db.execute(
        text("SELECT author_id FROM monitoring.incident_comments WHERE id = :cid AND incident_id = :iid"),
        {"cid": comment_id, "iid": incident_id},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    if row["author_id"] != viewer_id:
        raise HTTPException(
            status_code=403, detail="Нельзя удалить чужой комментарий")
    await db.execute(
        text("DELETE FROM monitoring.incident_comments WHERE id = :cid"), {
            "cid": comment_id}
    )
    await db.commit()
    return Response(status_code=204)
