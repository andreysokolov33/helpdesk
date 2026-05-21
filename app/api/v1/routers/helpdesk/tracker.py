from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import String, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import (
    RegisterCallRequest,
    RegisterCallResponse,
    TicketDetailResponse,
    TicketMarkReadRequest,
    TicketMessageItem,
    TicketMessagesResponse,
    TicketSendMessageResponse,
    TrackerTicketListItem,
    TrackerTicketListResponse,
)
from app.api.v1.routers.helpdesk import ticket_service as ticket_svc
from app.constants import (
    PRIORITY_DICT,
    SOURCE_DISPLAY,
    STATUS_DISPLAY,
    TRACKER_CLOSED_STATUSES,
    TRACKER_HELPDESK_LIST_SOURCES,
    TRACKER_OPEN_STATUSES,
)
from app.database import get_db
from app.models.oss import JurClientList
from app.models.users import (
    SkystreamUsers,
    TicketCategory,
    TrackerTicketLineHistory,
    TrackerTickets,
    User,
    UserDetails,
)

router = APIRouter(prefix="/v1/helpdesk/tracker", tags=["Helpdesk — трекер"])


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
) -> TrackerTicketListResponse:
    """
    Список тикетов `users.tracker_tickets` с пагинацией.
    По умолчанию только незакрытые (`closed=false`), источник lk / ks / abs.
    """
    status_as_text = cast(TrackerTickets.status, String)
    status_filter = (
        status_as_text.in_(TRACKER_CLOSED_STATUSES)
        if closed
        else status_as_text.in_(TRACKER_OPEN_STATUSES)
    )
    source_as_text = cast(TrackerTickets.source, String)
    source_filter = source_as_text.in_(TRACKER_HELPDESK_LIST_SOURCES)
    list_filter = and_(status_filter, source_filter)

    u = aliased(User)
    tc = aliased(TicketCategory)
    tcp = aliased(TicketCategory)
    assignee = aliased(SkystreamUsers)
    jur = aliased(JurClientList)

    ud_win = (
        select(
            UserDetails.user_id,
            UserDetails.surname,
            UserDetails.name,
            UserDetails.patronymic,
            func.row_number()
            .over(partition_by=UserDetails.user_id, order_by=UserDetails.id.desc())
            .label("rn"),
        ).where(UserDetails.is_actual.is_(True))
    ).subquery()
    ud1 = aliased(ud_win, name="ud1")

    count_stmt = select(func.count()).select_from(TrackerTickets).where(list_filter)
    total = int((await db.execute(count_stmt)).scalar_one())

    stmt = (
        select(
            TrackerTickets,
            u.login.label("subscriber_login"),
            u.is_juridical.label("sub_is_juridical"),
            ud1.c.surname.label("ud_surname"),
            ud1.c.name.label("ud_name"),
            ud1.c.patronymic.label("ud_patronymic"),
            jur.short_name_organization.label("jur_short_name"),
            tc.name.label("category_name"),
            tcp.name.label("category_parent_name"),
            assignee.full_name.label("assignee_name"),
            assignee.role.label("assignee_role"),
        )
        .outerjoin(u, and_(TrackerTickets.user_id == u.id, TrackerTickets.object_type == "user"))
        .outerjoin(ud1, and_(ud1.c.user_id == u.id, ud1.c.rn == 1))
        .outerjoin(jur, jur.id == u.juridical_id)
        .outerjoin(tc, TrackerTickets.category_id == tc.id)
        .outerjoin(tcp, tc.parent_id == tcp.id)
        .outerjoin(assignee, TrackerTickets.assigned_to == assignee.id)
        .where(list_filter)
        .order_by(
            TrackerTickets.updated_at.desc().nullslast(),
            TrackerTickets.date_of_create.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(stmt)
    items: list[TrackerTicketListItem] = []
    viewer_skystream_id = int(user["user_id"])
    for row in result.all():
        (
            tt,
            sub_login,
            sub_is_juridical,
            ud_surname,
            ud_name,
            ud_patronymic,
            jur_short,
            cat_name,
            cat_parent,
            assignee_name,
            assignee_role,
        ) = row

        assigned_id = int(tt.assigned_to) if tt.assigned_to is not None else None
        assignee_is_viewer = bool(assigned_id is not None and assigned_id == viewer_skystream_id)

        if cat_name and cat_parent:
            category_label = f"{cat_parent} / {cat_name}"
        else:
            category_label = cat_name or cat_parent

        st = str(tt.status)
        pr = str(tt.priority) if tt.priority is not None else None
        src = tt.source

        sub_name, profile_uid, sub_ij = _subscriber_list_fields(
            str(tt.object_type),
            int(tt.user_id) if tt.user_id is not None else None,
            sub_login,
            int(sub_is_juridical) if sub_is_juridical is not None else None,
            ud_surname,
            ud_name,
            ud_patronymic,
            jur_short,
        )

        items.append(
            TrackerTicketListItem(
                id=int(tt.id),
                title=tt.title,
                object_type=str(tt.object_type),
                status=st,
                status_label=STATUS_DISPLAY.get(st, st),
                priority=pr,
                priority_label=PRIORITY_DICT.get(pr, pr) if pr else None,
                support_line=int(tt.support_line),
                support_line_label=_support_line_label(int(tt.support_line)),
                source=src,
                source_label=SOURCE_DISPLAY.get(src or "call_center", src or "call_center"),
                category_label=category_label,
                user_id=int(tt.user_id) if tt.user_id is not None else None,
                subscriber_profile_user_id=profile_uid,
                subscriber_is_juridical=sub_ij,
                subscriber_name=sub_name or None,
                subscriber_login=sub_login,
                assignee_name=assignee_name,
                assignee_role=assignee_role,
                assignee_is_viewer=assignee_is_viewer,
                date_of_create=tt.date_of_create,
                updated_at=tt.updated_at,
            )
        )

    return TrackerTicketListResponse(total=total, page=page, per_page=per_page, items=items)


_CALL_PLACEHOLDER_TITLE = "Звонок"


@router.post("/register-call", response_model=RegisterCallResponse)
async def register_call(
    payload: RegisterCallRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> RegisterCallResponse:
    """
    Регистрация входящего звонка: создаёт тикет в users.tracker_tickets без категории и SLA.
    """
    body_text = payload.body.strip()
    if not body_text:
        raise HTTPException(status_code=400, detail="Укажите, что говорит клиент")

    caller_name: str | None = None
    if payload.subscriber_unknown:
        caller_name = (payload.caller_name or "").strip()
        if not caller_name:
            raise HTTPException(
                status_code=400,
                detail="Укажите, как представился клиент",
            )
        ticket_user_id = None
        person_type = "cs"
        station_id = None
        hotspot_id = None
    else:
        if payload.user_id is None:
            raise HTTPException(
                status_code=400,
                detail="Выберите абонента или отметьте «Не удалось определить»",
            )
        ticket_user_id = int(payload.user_id)
        person_type = "user"
        station_id = payload.station_id
        hotspot_id = payload.hotspot_id

    now = datetime.now(timezone.utc)
    author_id = int(user["user_id"])

    ticket = TrackerTickets(
        author=author_id,
        user_id=ticket_user_id,
        support_line=1,
        status="in_progress",
        title=_CALL_PLACEHOLDER_TITLE,
        body=body_text,
        priority="middle",
        source="call_center",
        complexity="L1",
        person_type=person_type,
        caller_name=caller_name,
        object_type="user",
        station_id=station_id,
        hotspot_id=hotspot_id,
        vno=1,
        updated_at=now,
    )
    db.add(ticket)
    await db.flush()

    db.add(
        TrackerTicketLineHistory(
            ticket_id=int(ticket.id),
            support_line=1,
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
            payload={"status": "in_progress", "source": "call_center"},
        )
    )
    await db.commit()

    return RegisterCallResponse(id=int(ticket.id))


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketDetailResponse:
    data = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    return TicketDetailResponse(**data)


@router.get("/{ticket_id}/messages", response_model=TicketMessagesResponse)
async def get_ticket_messages(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> TicketMessagesResponse:
    detail = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    mode = detail["chat_mode"]
    viewer_id = int(user["user_id"])

    if mode == "tracker":
        raw = await ticket_svc.load_tracker_messages(
            db, ticket_id, viewer_id, str(user.get("role") or "")
        )
    else:
        raw = await ticket_svc.load_mail_messages(
            db,
            ticket_id,
            detail.get("user_id"),
            viewer_id,
        )
        unread = [m["id"] for m in raw if m["side"] == "client" and not m.get("has_read") and m["id"] > 0]
        if unread:
            await ticket_svc.mark_mail_messages_read(db, ticket_id, viewer_id, unread)

    return TicketMessagesResponse(
        chat_mode=mode,
        messages=[TicketMessageItem(**m) for m in raw],
    )


@router.post("/{ticket_id}/messages/read")
async def mark_ticket_messages_read(
    ticket_id: int,
    payload: TicketMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_tracker_user),
) -> dict[str, str]:
    await ticket_svc.mark_mail_messages_read(
        db, ticket_id, int(user["user_id"]), payload.message_ids
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
) -> TicketSendMessageResponse:
    detail = await ticket_svc.load_ticket_detail(db, ticket_id, int(user["user_id"]))
    operator_id = int(user["user_id"])
    client_ip = request.client.host if request.client else "127.0.0.1"

    if detail["chat_mode"] == "tracker":
        raw = await ticket_svc.send_tracker_reply(db, ticket_id, operator_id, text)
    else:
        if not detail.get("user_id"):
            raise HTTPException(
                status_code=400,
                detail="Нельзя ответить: абонент не определён",
            )
        raw = await ticket_svc.send_mail_reply(
            db,
            ticket_id,
            int(detail["user_id"]),
            operator_id,
            text,
            client_ip=client_ip,
            file=file,
        )

    return TicketSendMessageResponse(message=TicketMessageItem(**raw))
