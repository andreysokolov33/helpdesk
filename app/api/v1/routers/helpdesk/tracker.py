from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.v1.routers.helpdesk.deps import require_tracker_user
from app.api.v1.routers.helpdesk.schemas import TrackerTicketListItem, TrackerTicketListResponse
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
from app.models.users import SkystreamUsers, TicketCategory, TrackerTickets, User, UserDetails

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
