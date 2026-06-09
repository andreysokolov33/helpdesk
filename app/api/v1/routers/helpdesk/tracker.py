from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.exc import NotSupportedError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import (
    LinkTicketSubscriberRequest,
    CloseTicketRequest,
    TransferTicketToEngineersRequest,
    RegisterCallRequest,
    RegisterCallResponse,
    TicketCategoriesResponse,
    TicketCategoryGroup,
    TicketCategoryLeaf,
    TicketDetailResponse,
    TicketCommentEditRequest,
    TicketCommentItem,
    TicketCommentSendResponse,
    TicketCommentsResponse,
    TicketMarkReadRequest,
    TicketMessageEditRequest,
    TicketMessageItem,
    TicketMessagesResponse,
    TicketPollSnapshot,
    TicketReadReceiptsResponse,
    TicketSendMessageResponse,
    HelpdeskMacroItem,
    HelpdeskMacrosResponse,
    TrackerTicketListItem,
    TrackerTicketListDigestResponse,
    TrackerTicketListResponse,
    TrackerTicketListStats,
)
from app.api.v1.routers.helpdesk import ticket_service as ticket_svc
from app.core.ticket_message_validation import html_to_plain_text, validate_ticket_message_text
from app.api.v1.routers.helpdesk.call_lead_html import build_connection_lead_html
from app.core.ticket_queue_state import (
    communication_state_from_v2,
    list_highlight_for_viewer,
    on_register_call_cs,
    on_register_new_subscriber_lead,
    on_register_partner_prospect,
    support_line_to_queue_line,
)
from app.constants import (
    COMMUNICATION_STATE_LABELS,
    PRIORITY_DICT,
    SOURCE_DISPLAY,
    STATUS_DISPLAY,
    TRACKER_QUEUE_LINE_DISPLAY,
)
from app.database import get_db
from app.models.users import TrackerTicketLineHistory, TrackerTickets

router = APIRouter(prefix="/v1/helpdesk/tracker", tags=["Helpdesk — трекер"])


@router.post("/{ticket_id}/attachments/upload")
async def upload_ticket_attachment(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    detail = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    token = await ticket_svc.save_attachment_temp(
        file,
        ticket_id=ticket_id,
        user_id=int(detail["user_id"]) if detail.get("user_id") is not None else None,
    )
    return token


def _support_line_label(line: int) -> str:
    if line == 1:
        return "КС"
    if line == 2:
        return "Инженеры"
    if line == 3:
        return "Партнёр"
    return str(line)


def _initial_letter_token(part: Optional[str]) -> str:
    s = (part or "").strip()
    if not s:
        return ""
    ch = s[0].upper()
    return f"{ch}."


def _format_phys_fio(surname: Optional[str], name: Optional[str], patronymic: Optional[str]) -> str:
    """Формат «Иванов И.И.» из users.user_details."""
    sur = (surname or "").strip()
    ini = f"{_initial_letter_token(name)}{_initial_letter_token(patronymic)}".strip()
    if sur and ini:
        return f"{sur} {ini}"
    if sur:
        return sur
    if ini:
        return ini
    return ""


def _subscriber_list_fields(
    object_type: str,
    user_id: Optional[int],
    sub_login: Optional[str],
    is_juridical: Optional[int],
    ud_surname: Optional[str],
    ud_name: Optional[str],
    ud_patronymic: Optional[str],
    jur_short: Optional[str],
) -> tuple[str, Optional[int], int]:
    """
    (отображаемое имя, user_id для ссылки /users/{id} или None, is_juridical для UI).
    Для object_type != user ссылка не нужна.
    """
    if object_type != "user" or user_id is None:
        return ("", None, 0)
    uid = int(user_id)
    ij = int(is_juridical or 0)
    login = (sub_login or "").strip()

    if ij == 2:
        org = (jur_short or "").strip()
        display = org or login or f"#{uid}"
        return (display, uid, 2)

    fio = _format_phys_fio(ud_surname, ud_name, ud_patronymic)
    if fio:
        return (fio, uid, ij)
    display = login or f"#{uid}"
    return (display, uid, ij)


@router.get("/list", response_model=TrackerTicketListResponse)
async def list_tracker_tickets(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Размер страницы"),
    closed: bool = Query(
        False,
        description="True — только закрытые/терминальные статусы; False — открытые (TRACKER_OPEN_STATUSES)",
    ),
    subscriber_q: Optional[str] = Query(
        None,
        description="Поиск по абоненту: ФИО, id, логин",
    ),
    date_from: Optional[date] = Query(
        None,
        description="Дата с (открытие для открытых, закрытие для закрытых)",
    ),
    date_to: Optional[date] = Query(
        None,
        description="Дата по включительно",
    ),
) -> TrackerTicketListResponse:
    """
    Список тикетов `users.tracker_tickets` с пагинацией и tier-сортировкой (персонально по viewer_id).
    По умолчанию только незакрытые (`closed=false`), источники lk / call_center / abs.
    """
    viewer_skystream_id = int(user["user_id"])

    def _is_stale_prepared_cache(exc: BaseException) -> bool:
        cur: BaseException | None = exc
        while cur is not None:
            if "InvalidCachedStatement" in type(cur).__name__:
                return True
            cur = cur.__cause__ or cur.__context__
        return False

    total = 0
    rows: list[dict[str, Any]] = []
    list_stats: dict[str, float | None] = {"avg_rating": None, "avg_rating_mine": None}
    for attempt in range(2):
        try:
            total, rows, list_stats = await ticket_svc.fetch_tracker_list_page(
                db,
                viewer_id=viewer_skystream_id,
                closed=closed,
                page=page,
                per_page=per_page,
                subscriber_q=subscriber_q,
                date_from=date_from,
                date_to=date_to,
            )
            break
        except NotSupportedError as exc:
            if attempt == 0 and _is_stale_prepared_cache(exc):
                continue
            raise

    items: list[TrackerTicketListItem] = []
    for m in rows:
        sub_login = m.get("subscriber_login")
        sub_is_juridical = m.get("sub_is_juridical")
        ud_surname = m.get("ud_surname")
        ud_name = m.get("ud_name")
        ud_patronymic = m.get("ud_patronymic")
        jur_short = m.get("jur_short_name")
        cat_name = m.get("category_name")
        cat_parent = m.get("category_parent_name")
        assignee_name = m.get("assignee_name")
        assignee_role = m.get("assignee_role")
        has_unread = bool(m.get("calc_has_unread"))
        queue_line = str(m.get("queue_line") or support_line_to_queue_line(int(m.get("support_line") or 1)))
        action_by = str(m.get("action_by") or "cs")
        chat_turn = str(m.get("chat_turn") or "staff")
        st = str(m["status"])
        src = m.get("source")

        queue_snap = {
            "queue_line": queue_line,
            "action_by": action_by,
            "chat_turn": chat_turn,
            "action_since": m.get("action_since"),
        }
        highlight = list_highlight_for_viewer(
            queue_snap,
            viewer_role=str(user.get("role") or "support"),
            has_unread=has_unread,
            workflow_status=st,
            source=str(src or "call_center"),
            support_line=int(m.get("support_line") or 1),
        )
        comm_state = communication_state_from_v2(
            chat_turn, action_by, source=str(src or "call_center"),
        )
        if comm_state is None and highlight == "ops":
            comm_label = STATUS_DISPLAY.get(st, st)
        else:
            comm_label = (
                COMMUNICATION_STATE_LABELS.get(comm_state) if comm_state else None
            )

        owner_id = int(m["assigned_to"]) if m.get("assigned_to") is not None else None
        assignee_is_viewer = bool(owner_id is not None and owner_id == viewer_skystream_id)

        if cat_name and cat_parent:
            category_label = f"{cat_parent} / {cat_name}"
        else:
            category_label = cat_name or cat_parent

        pr = str(m["priority"]) if m.get("priority") is not None else None

        sub_name, profile_uid, sub_ij = _subscriber_list_fields(
            str(m["object_type"]),
            int(m["user_id"]) if m.get("user_id") is not None else None,
            sub_login,
            int(sub_is_juridical) if sub_is_juridical is not None else None,
            ud_surname,
            ud_name,
            ud_patronymic,
            jur_short,
        )

        items.append(
            TrackerTicketListItem(
                id=int(m["id"]),
                title=m["title"],
                object_type=str(m["object_type"]),
                status=st,
                status_label=STATUS_DISPLAY.get(st, st),
                priority=pr,
                priority_label=PRIORITY_DICT.get(pr, pr) if pr else None,
                support_line=int(m["support_line"]),
                support_line_label=TRACKER_QUEUE_LINE_DISPLAY.get(
                    queue_line, _support_line_label(int(m["support_line"])),
                ),
                queue_line=queue_line,
                action_by=action_by,
                chat_turn=chat_turn,
                action_since=m.get("action_since"),
                list_highlight=highlight,
                source=src,
                source_label=SOURCE_DISPLAY.get(src or "call_center", src or "call_center"),
                category_label=category_label,
                user_id=int(m["user_id"]) if m.get("user_id") is not None else None,
                subscriber_profile_user_id=profile_uid,
                subscriber_is_juridical=sub_ij,
                subscriber_name=sub_name or None,
                subscriber_login=sub_login,
                assignee_name=assignee_name,
                assignee_role=assignee_role,
                assignee_is_viewer=assignee_is_viewer,
                assigned_to=int(m["assigned_to"]) if m.get("assigned_to") is not None else None,
                has_unread=has_unread,
                communication_state=comm_state,
                communication_label=comm_label,
                date_of_create=m["date_of_create"],
                updated_at=m.get("updated_at"),
                date_of_close=m.get("date_of_close"),
                rating=int(m["rating"]) if m.get("rating") is not None else None,
                rating_comment=m.get("rating_comment"),
            )
        )

    stats = None
    if closed:
        stats = TrackerTicketListStats(
            avg_rating=list_stats.get("avg_rating"),
            avg_rating_mine=list_stats.get("avg_rating_mine"),
        )

    return TrackerTicketListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
        stats=stats,
    )


@router.get("/list/digest", response_model=TrackerTicketListDigestResponse)
async def list_tracker_tickets_digest(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    closed: bool = Query(False),
    subscriber_q: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    digest: Optional[str] = Query(
        None,
        description="Отпечаток с прошлого поллинга; при совпадении changed=false",
    ),
) -> TrackerTicketListDigestResponse:
    """
    Лёгкий поллинг списка /tickets: без join абонентов и категорий.
    При changed=false клиент не вызывает GET /list.
    """
    data = await ticket_svc.fetch_tracker_list_digest(
        db,
        viewer_id=int(user["user_id"]),
        closed=closed,
        page=page,
        per_page=per_page,
        subscriber_q=subscriber_q,
        date_from=date_from,
        date_to=date_to,
        client_digest=(digest or "").strip() or None,
    )
    return TrackerTicketListDigestResponse(**data)


_CALL_TITLE_EXISTING = "Звонок"
_CALL_TITLE_NEW_SUBSCRIBER = "Новое подключение — абонент"
_CALL_TITLE_NEW_PARTNER = "Новое подключение — партнёр"


@router.post("/register-call", response_model=RegisterCallResponse)
async def register_call(
    payload: RegisterCallRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> RegisterCallResponse:
    """
    Регистрация входящего звонка: абонент в базе, новый абонент или новый партнёр.
    """
    kind = payload.connection_kind
    now = datetime.now(timezone.utc)
    author_id = int(user["user_id"])

    if kind == "existing":
        body_text = (payload.body or "").strip()
        ticket_user_id = int(payload.user_id)  # type: ignore[arg-type]
        caller_name = None
        person_type = "user"
        object_type = "user"
        station_id = payload.station_id
        hotspot_id = payload.hotspot_id
        support_line = 1
        status = "in_progress"
        assigned_to = author_id
        title = _CALL_TITLE_EXISTING
        queue_snap = on_register_call_cs(at=now)
    elif kind == "new_subscriber":
        lead = payload.lead
        assert lead is not None
        body_text = build_connection_lead_html(
            kind="subscriber",
            full_name=lead.full_name,
            address=lead.address,
            phone=lead.phone,
            sees_network=lead.sees_network,
            notes=lead.notes,
        )
        ticket_user_id = None
        caller_name = lead.full_name.strip()
        person_type = "cs"
        object_type = "other"
        station_id = None
        hotspot_id = None
        support_line = 1
        status = "in_progress"
        assigned_to = author_id
        title = _CALL_TITLE_NEW_SUBSCRIBER
        queue_snap = on_register_new_subscriber_lead(at=now)
    else:
        lead = payload.lead
        assert lead is not None
        body_text = build_connection_lead_html(
            kind="partner",
            full_name=lead.full_name,
            address=lead.address,
            phone=lead.phone,
            potential_subscribers=lead.potential_subscribers,
            plans_new_station=lead.plans_new_station,
            notes=lead.notes,
        )
        ticket_user_id = None
        caller_name = lead.full_name.strip()
        person_type = "partner"
        object_type = "other"
        station_id = None
        hotspot_id = None
        support_line = 4
        status = "pending"
        assigned_to = None
        title = _CALL_TITLE_NEW_PARTNER
        queue_snap = on_register_partner_prospect(at=now)

    ticket = TrackerTickets(
        author=author_id,
        assigned_to=assigned_to,
        engineer_id=None,
        user_id=ticket_user_id,
        support_line=support_line,
        status=status,
        title=title,
        body=body_text,
        priority="middle",
        source="call_center",
        complexity="L1",
        person_type=person_type,
        caller_name=caller_name,
        object_type=object_type,
        station_id=station_id,
        hotspot_id=hotspot_id,
        vno=1,
        updated_at=now,
        queue_line=queue_snap["queue_line"],
        action_by=queue_snap["action_by"],
        chat_turn=queue_snap["chat_turn"],
        action_since=queue_snap["action_since"],
    )
    db.add(ticket)
    await db.flush()

    db.add(
        TrackerTicketLineHistory(
            ticket_id=int(ticket.id),
            support_line=support_line,
            start_time=now,
            changed_by=author_id,
            state="active",
        )
    )
    db.add(
        TrackerTicketLineHistory(
            ticket_id=int(ticket.id),
            support_line=None,
            start_time=now,
            changed_by=author_id,
            event_type="created",
            payload={
                "status": status,
                "source": "call_center",
                "connection_kind": kind,
            },
        )
    )
    await db.commit()

    return RegisterCallResponse(id=int(ticket.id))


@router.get("/categories", response_model=TicketCategoriesResponse)
async def list_ticket_categories(
    db: AsyncSession = Depends(get_db),
    _user: dict[str, Any] = Depends(require_tracker_user),
    source: Optional[str] = Query(
        None,
        description="Источник тикета (lk, call_center, partner, …) — для выбора справочника",
    ),
) -> TicketCategoriesResponse:
    catalog = ticket_svc.catalog_source_for_ticket(source)
    raw = await ticket_svc.load_ticket_categories(db, catalog_source=catalog)
    items = [
        TicketCategoryGroup(
            id=g["id"],
            name=g["name"],
            slug=g["slug"],
            children=[TicketCategoryLeaf(**c) for c in g.get("children", [])],
        )
        for g in raw
    ]
    return TicketCategoriesResponse(catalog_source=catalog, items=items)


@router.get("/macros", response_model=HelpdeskMacrosResponse)
async def list_helpdesk_macros(
    db: AsyncSession = Depends(get_db),
    _user: dict[str, Any] = Depends(require_tracker_user),
) -> HelpdeskMacrosResponse:
    raw = await ticket_svc.load_helpdesk_macros(db)
    return HelpdeskMacrosResponse(items=[HelpdeskMacroItem(**m) for m in raw])


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    data = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    return TicketDetailResponse(**data)


@router.patch("/{ticket_id}/subscriber", response_model=TicketDetailResponse)
async def link_ticket_subscriber(
    ticket_id: int,
    payload: LinkTicketSubscriberRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    """Привязать абонента к тикету, у которого user_id ещё не задан."""
    data = await ticket_svc.link_ticket_subscriber(
        db,
        ticket_id,
        int(payload.user_id),
        int(user["user_id"]),
    )
    return TicketDetailResponse(**data)


@router.post("/{ticket_id}/transfer-to-engineers", response_model=TicketDetailResponse)
async def transfer_ticket_to_engineers(
    ticket_id: int,
    payload: TransferTicketToEngineersRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    """Передача тикета на линию инженеров (support_line=2) без смены категории КС."""
    data = await ticket_svc.transfer_ticket_to_engineers(
        db,
        ticket_id,
        payload.category_id,
        payload.comment,
        int(user["user_id"]),
    )
    return TicketDetailResponse(**data)


@router.post("/{ticket_id}/take-back-to-ks", response_model=TicketDetailResponse)
async def take_ticket_back_to_ks(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    """Вернуть тикет на линию КС (support_line=1) и взять в работу."""
    data = await ticket_svc.take_ticket_back_to_ks(
        db,
        ticket_id,
        int(user["user_id"]),
    )
    return TicketDetailResponse(**data)


@router.post("/{ticket_id}/close", response_model=TicketDetailResponse)
async def close_ticket(
    ticket_id: int,
    payload: CloseTicketRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    """Заглушка: закрытие с классификацией отключено в UI КС (ticket_svc.close_ticket сохранён)."""
    raise HTTPException(
        status_code=403,
        detail="Закрытие тикета из интерфейса КС временно недоступно",
    )
    # data = await ticket_svc.close_ticket(
    #     db,
    #     ticket_id,
    #     int(payload.category_id),
    #     payload.comment,
    #     int(user["user_id"]),
    # )
    # return TicketDetailResponse(**data)


@router.post("/{ticket_id}/reopen", response_model=TicketDetailResponse)
async def reopen_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    """Переоткрытие тикета в течение 24 часов после закрытия."""
    data = await ticket_svc.reopen_ticket(db, ticket_id, int(user["user_id"]))
    return TicketDetailResponse(**data)


@router.get("/{ticket_id}/comments", response_model=TicketCommentsResponse)
async def get_ticket_comments(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    limit: int = Query(20, ge=1, le=100, description="Размер порции"),
    before_id: int | None = Query(None, ge=1, description="Комментарии старее id"),
    after_id: int | None = Query(None, ge=1, description="Комментарии новее id"),
    since_id: int = Query(0, ge=0, description="Поллинг: id > since_id"),
) -> TicketCommentsResponse:
    if before_id is not None and after_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Укажите не более одного из before_id и after_id",
        )
    if since_id > 0 and (before_id is not None or after_id is not None):
        raise HTTPException(
            status_code=400,
            detail="since_id нельзя сочетать с before_id или after_id",
        )
    raw, has_older, has_newer = await ticket_svc.list_ticket_comments(
        db,
        ticket_id,
        int(user["user_id"]),
        limit=limit,
        before_id=before_id,
        after_id=after_id,
        since_id=since_id,
    )
    return TicketCommentsResponse(
        comments=[TicketCommentItem(**c) for c in raw],
        has_older=has_older,
        has_newer=has_newer,
    )


@router.post("/{ticket_id}/comments", response_model=TicketCommentSendResponse)
async def send_ticket_comment(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    text: str = Form(""),
) -> TicketCommentSendResponse:
    raw = await ticket_svc.send_ticket_comment(
        db,
        ticket_id,
        int(user["user_id"]),
        text,
    )
    return TicketCommentSendResponse(comment=TicketCommentItem(**raw))


@router.patch("/{ticket_id}/comments/{comment_id}", response_model=TicketCommentItem)
async def edit_ticket_comment(
    ticket_id: int,
    comment_id: int,
    payload: TicketCommentEditRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketCommentItem:
    raw = await ticket_svc.edit_ticket_comment(
        db,
        ticket_id,
        comment_id,
        int(user["user_id"]),
        payload.text,
    )
    return TicketCommentItem(**raw)


@router.delete("/{ticket_id}/comments/{comment_id}")
async def delete_ticket_comment(
    ticket_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> dict[str, str]:
    await ticket_svc.delete_ticket_comment(
        db,
        ticket_id,
        comment_id,
        int(user["user_id"]),
    )
    return {"status": "ok"}


@router.get("/{ticket_id}/messages", response_model=TicketMessagesResponse)
async def get_ticket_messages(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    limit: int = Query(20, ge=1, le=100, description="Размер порции"),
    before_id: int | None = Query(None, ge=1, description="Сообщения старее id (скролл вверх)"),
    after_id: int | None = Query(None, ge=1, description="Сообщения новее id (скролл вниз)"),
    around_id: int | None = Query(None, ge=1, description="Окно вокруг сообщения (переход по цитате)"),
    since_id: int = Query(0, ge=0, description="Поллинг: только сообщения с id > since_id"),
) -> TicketMessagesResponse:
    cursors = sum(1 for x in (before_id, after_id, around_id) if x is not None)
    if cursors > 1:
        raise HTTPException(
            status_code=400,
            detail="Укажите не более одного из before_id, after_id, around_id",
        )
    if since_id > 0 and cursors > 0:
        raise HTTPException(
            status_code=400,
            detail="since_id нельзя сочетать с before_id, after_id или around_id",
        )

    raw, mode, receipts, read_by, has_older, has_newer, ticket_snap = await ticket_svc.list_ticket_messages(
        db,
        ticket_id,
        int(user["user_id"]),
        str(user.get("role") or ""),
        limit=limit,
        before_id=before_id,
        after_id=after_id,
        around_id=around_id,
        since_id=since_id,
    )
    return TicketMessagesResponse(
        chat_mode=mode,
        messages=[TicketMessageItem(**m) for m in raw],
        read_receipts=receipts,
        read_by_receipts=read_by,
        has_older=has_older,
        has_newer=has_newer,
        ticket=TicketPollSnapshot(**ticket_snap) if ticket_snap else None,
    )


@router.get("/{ticket_id}/messages/reads", response_model=TicketReadReceiptsResponse)
async def get_ticket_message_reads(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketReadReceiptsResponse:
    mode, receipts, read_by = await ticket_svc.get_ticket_read_receipts(
        db,
        ticket_id,
        int(user["user_id"]),
    )
    return TicketReadReceiptsResponse(
        chat_mode=mode,
        read_receipts=receipts,
        read_by_receipts=read_by,
    )


@router.post("/{ticket_id}/messages/read")
async def mark_ticket_messages_read(
    ticket_id: int,
    payload: TicketMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> dict[str, str]:
    detail = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    if detail["chat_mode"] == "tracker":
        await ticket_svc.mark_tracker_messages_read(
            db, ticket_id, int(user["user_id"]), payload.message_ids
        )
    else:
        await ticket_svc.mark_mail_messages_read(
            db, ticket_id, int(user["user_id"]), payload.message_ids
        )
    return {"status": "ok"}


@router.patch("/{ticket_id}/messages/{message_id}", response_model=TicketMessageItem)
async def edit_ticket_message(
    ticket_id: int,
    message_id: int,
    payload: TicketMessageEditRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketMessageItem:
    if html_to_plain_text(payload.text):
        validation_err = validate_ticket_message_text(payload.text, has_attachments=False)
        if validation_err:
            raise HTTPException(status_code=400, detail=validation_err)
    raw = await ticket_svc.edit_ticket_message(
        db,
        ticket_id,
        message_id,
        int(user["user_id"]),
        str(user.get("role") or ""),
        payload.text,
    )
    return TicketMessageItem(**raw)


@router.delete("/{ticket_id}/messages/{message_id}")
async def delete_ticket_message(
    ticket_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> dict[str, str]:
    await ticket_svc.delete_ticket_message(db, ticket_id, message_id, int(user["user_id"]))
    return {"status": "ok"}


@router.delete("/{ticket_id}/messages/{message_id}/attachments/{attachment_id}")
async def detach_message_attachment(
    ticket_id: int,
    message_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> dict[str, str]:
    await ticket_svc.detach_ticket_attachment(
        db,
        ticket_id=ticket_id,
        message_id=message_id,
        attachment_id=attachment_id,
        operator_id=int(user["user_id"]),
    )
    return {"status": "ok"}


@router.post("/{ticket_id}/messages", response_model=TicketSendMessageResponse)
async def send_ticket_message(
    ticket_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
    text: str = Form(""),
    file: UploadFile | None = File(None),
    upload_tokens: str = Form("[]"),
    reply_to_id: int | None = Form(None),
) -> TicketSendMessageResponse:
    detail = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    operator_id = int(user["user_id"])
    client_ip = request.client.host if request.client else "127.0.0.1"

    operator_role = str(user.get("role") or "")
    reply_id = int(reply_to_id) if reply_to_id and reply_to_id > 0 else None
    try:
        tokens_list = json.loads(upload_tokens or "[]")
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный upload_tokens")
    if not isinstance(tokens_list, list) or not all(isinstance(x, str) for x in tokens_list):
        raise HTTPException(status_code=400, detail="Некорректный upload_tokens")

    attachments = ticket_svc.finalize_upload_tokens(tokens_list, ticket_id=ticket_id) if tokens_list else []

    # legacy single-file path: still supported, but will be stored as attachment too
    if file and file.filename:
        tmp = await ticket_svc.save_attachment_temp(
            file,
            ticket_id=ticket_id,
            user_id=int(detail["user_id"]) if detail.get("user_id") is not None else None,
        )
        attachments += ticket_svc.finalize_upload_tokens([tmp["token"]], ticket_id=ticket_id)

    validation_err = validate_ticket_message_text(text, has_attachments=bool(attachments))
    if validation_err:
        raise HTTPException(status_code=400, detail=validation_err)

    batches: list[list[dict[str, Any]]] = []
    for i in range(0, len(attachments), 10):
        batches.append(attachments[i : i + 10])
    if not batches:
        batches = [[]]

    created: list[dict[str, Any]] = []
    for idx, att in enumerate(batches):
        body = text if idx == 0 else ""
        if detail["chat_mode"] == "tracker":
            raw = await ticket_svc.send_tracker_reply(
                db,
                ticket_id,
                operator_id,
                body,
                operator_role=operator_role,
                reply_to_id=reply_id if idx == 0 else None,
                attachments=att,
            )
        else:
            if not detail.get("user_id"):
                raise HTTPException(status_code=400, detail="Нельзя ответить: абонент не определён")
            raw = await ticket_svc.send_mail_reply(
                db,
                ticket_id,
                int(detail["user_id"]),
                operator_id,
                body,
                client_ip=client_ip,
                file=None,
                operator_role=operator_role,
                reply_to_id=reply_id if idx == 0 else None,
                attachments=att,
            )
        created.append(raw)

    items = [TicketMessageItem(**m) for m in created]
    return TicketSendMessageResponse(message=items[0], messages=items)
