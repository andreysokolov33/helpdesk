"""Карточка тикета: шапка, сообщения user_mail / tracker_messages, отправка, вложения."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import jwt
from fastapi import HTTPException, UploadFile
from sqlalchemy import Boolean, DateTime, String, case, cast, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.constants import (
    COMMUNICATION_STATE_LABELS,
    PRIORITY_DICT,
    SOURCE_DISPLAY,
    STATUS_DISPLAY,
    SUPPORT_LINE_DISPLAY,
    TRACKER_ACTION_BY_DISPLAY,
    TRACKER_CHAT_TURN_DISPLAY,
    TRACKER_CLOSED_STATUSES,
    TRACKER_HELPDESK_LIST_SOURCES,
    TRACKER_OPEN_STATUSES,
    TRACKER_OPERATIONAL_WAIT_STATUSES,
    TRACKER_QUEUE_LINE_DISPLAY,
    is_internal_staff_chat_source,
    is_subscriber_chat_source,
    is_visible_to_cs_support,
)
from app.models.users import TrackerTickets
from app.models.users import (
    TrackerComments,
    TrackerMessageAttachment,
    TrackerMessages,
    TrackerTicketLineHistory,
    UserMailAttachment,
)
from app.api.v1.routers.helpdesk import user_profile_service as profile_svc
from app.database import redis_client
from app.core.ticket_queue_state import (
    StaffParty,
    TicketQueueSnapshot,
    TrackerChatTurn,
    TrackerQueueLine,
    communication_state_from_v2,
    list_highlight_for_viewer,
    on_escalate_to_engineers,
    on_internal_staff_message,
    on_register_call_cs,
    on_return_to_cs,
    on_staff_public_reply,
    on_subscriber_public_message,
    queue_line_to_legacy_support_line,
    support_line_to_queue_line,
)

STAFF_READ_PERSON_TYPES = ("skystream", "call_centre")
STAFF_OUTBOUND_SIDES = frozenset({"me", "support", "engineer"})
_MAIL_IS_CLIENT = """
    CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
         THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
         ELSE COALESCE(um.answer, 0) END = 0
"""
_TICKET_TBL = "users.tracker_tickets"
_STAFF_READ_IN_SQL = ", ".join(f"'{t}'" for t in STAFF_READ_PERSON_TYPES)


def _coerce_queue_line(row: dict[str, Any]) -> TrackerQueueLine:
    raw = row.get("queue_line")
    if raw in ("cs", "engineers", "partner"):
        return raw
    return support_line_to_queue_line(int(row.get("support_line") or 1))


def _coerce_chat_turn(row: dict[str, Any]) -> TrackerChatTurn:
    raw = row.get("chat_turn")
    if raw in ("staff", "subscriber"):
        return raw  # type: ignore[return-value]
    return "subscriber"


def _staff_party_from_role(
    operator_role: str | None,
    *,
    queue_line: TrackerQueueLine,
) -> StaffParty:
    role = (operator_role or "").strip().lower()
    if role == "engineer":
        return "engineers"
    if role == "support":
        return "cs"
    return "engineers" if queue_line == "engineers" else "cs"


async def _load_ticket_queue_row(db: AsyncSession, ticket_id: int) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                """
                SELECT support_line,
                       COALESCE(source, 'call_center') AS source,
                       status::text AS status,
                       queue_line::text AS queue_line,
                       action_by::text AS action_by,
                       chat_turn::text AS chat_turn,
                       action_since
                FROM users.tracker_tickets
                WHERE id = :id
                """
            ),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return dict(row)


async def _fetch_last_public_message_meta(
    db: AsyncSession,
    ticket_id: int,
    *,
    source: str | None,
) -> tuple[bool, datetime] | None:
    """Последнее публичное сообщение: (от абонента, время)."""
    mode = chat_mode_for_source(source)
    if mode == "mail":
        row = (
            await db.execute(
                text(
                    """
                    WITH msgs AS (
                        SELECT COALESCE(um.date_tz, to_timestamp(um.date)) AS ts,
                               (
                                   COALESCE(um.answer, 0) = 0
                                   OR lower(COALESCE(um.person_type, '')) = 'user'
                               ) AS from_subscriber
                        FROM users.user_mail um
                        WHERE um.ticket_id = :tid
                        UNION ALL
                        SELECT COALESCE(um.date_tz, to_timestamp(um.date)),
                               (
                                   COALESCE(um.answer, 0) = 0
                                   OR lower(COALESCE(um.person_type, '')) = 'user'
                               )
                        FROM users.tracker_ticket_mail_links l
                        JOIN users.user_mail um ON um.id = l.user_mail_id
                        WHERE l.ticket_id = :tid
                    )
                    SELECT from_subscriber, ts
                    FROM msgs
                    WHERE ts IS NOT NULL
                    ORDER BY ts DESC
                    LIMIT 1
                    """
                ),
                {"tid": ticket_id},
            )
        ).mappings().first()
    else:
        row = (
            await db.execute(
                text(
                    """
                    SELECT lower(COALESCE(tm.person_type, 'skystream')) AS pt,
                           tm.created_at AS ts
                    FROM users.tracker_messages tm
                    WHERE tm.ticket_id = :tid
                    ORDER BY tm.created_at DESC, tm.id DESC
                    LIMIT 1
                    """
                ),
                {"tid": ticket_id},
            )
        ).mappings().first()
        if row and row.get("ts") is not None:
            return bool(row["pt"] == "user"), _coerce_utc(row["ts"])
        return None
    if not row or row.get("ts") is None:
        return None
    return bool(row["from_subscriber"]), _coerce_utc(row["ts"])


async def _fetch_last_internal_staff_message_meta(
    db: AsyncSession,
    ticket_id: int,
    *,
    queue_line: TrackerQueueLine,
) -> tuple[StaffParty, datetime] | None:
    """Последнее staff-сообщение tracker_messages (call_center / abs)."""
    row = (
        await db.execute(
            text(
                """
                SELECT tm.created_at AS ts,
                       lower(COALESCE(su.role, '')) AS author_role
                FROM users.tracker_messages tm
                LEFT JOIN users.skystream_users su ON su.id = tm.author_id
                WHERE tm.ticket_id = :tid
                  AND lower(COALESCE(tm.person_type, 'skystream')) <> 'user'
                ORDER BY tm.created_at DESC, tm.id DESC
                LIMIT 1
                """
            ),
            {"tid": ticket_id},
        )
    ).mappings().first()
    if not row or row.get("ts") is None:
        return None
    party = _staff_party_from_role(str(row.get("author_role") or ""), queue_line=queue_line)
    return party, _coerce_utc(row["ts"])


def _staff_reply_workflow_status(current_status: str | None) -> str | None:
    """SLA «ожидание клиента» не затирает операционные паузы (запчасти, handoff КС)."""
    st = (current_status or "").strip()
    if st in TRACKER_OPERATIONAL_WAIT_STATUSES or st == "cc_handover":
        return None
    if st in TRACKER_CLOSED_STATUSES:
        return None
    return "waiting_client"


def _subscriber_reply_workflow_status(current_status: str | None) -> str | None:
    st = (current_status or "").strip()
    if st in TRACKER_CLOSED_STATUSES:
        return None
    if st in TRACKER_OPERATIONAL_WAIT_STATUSES or st == "cc_handover":
        return None
    if st in ("waiting_client", "pending", "open"):
        return "in_progress"
    return None


async def reconcile_ticket_queue_from_thread(
    db: AsyncSession,
    ticket_id: int,
    *,
    source: str | None,
) -> None:
    """Синхронизировать v2 с последним сообщением (lk — с абонентом; call_center/abs — КС↔инженеры)."""
    row = await _load_ticket_queue_row(db, ticket_id)
    if str(row.get("action_by") or "") == "external":
        return

    src = str(source or row.get("source") or "call_center")
    queue_line = _coerce_queue_line(row)
    chat_turn = _coerce_chat_turn(row)
    action_since = row.get("action_since")
    if action_since is not None:
        action_since = _coerce_utc(action_since)

    if is_internal_staff_chat_source(src):
        meta = await _fetch_last_internal_staff_message_meta(
            db, ticket_id, queue_line=queue_line,
        )
        if not meta:
            return
        author_party, msg_at = meta
        msg_at = _coerce_utc(msg_at)
        expected_action = "engineers" if author_party == "cs" else "cs"
        current_action = str(row.get("action_by") or "")
        if (
            chat_turn == "staff"
            and current_action == expected_action
            and action_since is not None
            and action_since >= msg_at
        ):
            return
        if chat_turn == "staff" and current_action != expected_action:
            snap = on_internal_staff_message(author_party, queue_line, at=msg_at)
            await _apply_queue_snapshot(db, ticket_id, snap, status=None)
            await db.commit()
            return
        if action_since is not None and action_since > msg_at:
            return
        if (
            chat_turn == "staff"
            and current_action == expected_action
            and action_since is not None
            and msg_at <= action_since
        ):
            return
        snap = on_internal_staff_message(author_party, queue_line, at=msg_at)
        await _apply_queue_snapshot(db, ticket_id, snap, status=None)
        await db.commit()
        return

    if not is_subscriber_chat_source(src):
        return

    meta = await _fetch_last_public_message_meta(db, ticket_id, source=src)
    if not meta:
        return

    from_subscriber, msg_at = meta
    msg_at = _coerce_utc(msg_at)
    current_status = str(row.get("status") or "")

    if from_subscriber:
        if action_since is not None and action_since > msg_at:
            return
        if chat_turn == "staff" and action_since is not None and msg_at <= action_since:
            return
        snap = on_subscriber_public_message(queue_line, at=msg_at)
        await _apply_queue_snapshot(
            db,
            ticket_id,
            snap,
            status=_subscriber_reply_workflow_status(current_status),
            last_client_message_at=msg_at,
        )
        await db.commit()
        return

    if action_since is not None and action_since > msg_at:
        return
    if chat_turn == "subscriber" and action_since is not None and msg_at <= action_since:
        return
    snap = on_staff_public_reply(queue_line, at=msg_at)
    await _apply_queue_snapshot(
        db,
        ticket_id,
        snap,
        status=_staff_reply_workflow_status(current_status),
    )
    await db.commit()


async def reconcile_open_tickets_on_list_page(
    db: AsyncSession,
    rows: list[dict[str, Any]],
) -> None:
    """Синхронизировать v2-очередь с лентой перед отдачей списка (как в карточке тикета)."""
    for row in rows:
        status = str(row.get("status") or "").strip()
        if status in TRACKER_CLOSED_STATUSES:
            continue
        ticket_id = int(row["id"])
        await reconcile_ticket_queue_from_thread(
            db,
            ticket_id,
            source=row.get("source"),
        )


async def _apply_queue_snapshot(
    db: AsyncSession,
    ticket_id: int,
    snapshot: TicketQueueSnapshot,
    *,
    status: str | None = None,
    last_client_message_at: datetime | None = None,
    sync_support_line: bool = True,
) -> None:
    """Обновить v2-колонки очереди (+ legacy support_line при необходимости)."""
    params: dict[str, Any] = {
        "ticket_id": ticket_id,
        "queue_line": snapshot["queue_line"],
        "action_by": snapshot["action_by"],
        "chat_turn": snapshot["chat_turn"],
        "action_since": snapshot["action_since"],
    }
    sets = [
        "queue_line = CAST(:queue_line AS users.tracker_queue_line)",
        "action_by = CAST(:action_by AS users.tracker_action_by)",
        "chat_turn = CAST(:chat_turn AS users.tracker_chat_turn)",
        "action_since = :action_since",
        "updated_at = NOW()",
    ]
    if sync_support_line:
        params["support_line"] = queue_line_to_legacy_support_line(snapshot["queue_line"])
        sets.append("support_line = :support_line")
    if status is not None:
        params["status"] = status
        sets.append("status = CAST(:status AS users.tracker_status)")
    if last_client_message_at is not None:
        params["last_client_message_at"] = last_client_message_at
        sets.append("last_client_message_at = :last_client_message_at")
    await db.execute(
        text(
            f"""
            UPDATE users.tracker_tickets
            SET {", ".join(sets)}
            WHERE id = :ticket_id
            """
        ),
        params,
    )


async def _apply_staff_chat_queue_update(
    db: AsyncSession,
    ticket_id: int,
    *,
    operator_role: str | None = None,
    at: datetime | None = None,
) -> None:
    """Обновить v2 после сообщения staff: lk → абонент; call_center/abs → КС↔инженеры."""
    row = await _load_ticket_queue_row(db, ticket_id)
    now = at or datetime.now(timezone.utc)
    source = str(row.get("source") or "call_center")
    queue_line = _coerce_queue_line(row)

    if is_internal_staff_chat_source(source):
        party = _staff_party_from_role(operator_role, queue_line=queue_line)
        snapshot = on_internal_staff_message(party, queue_line, at=now)
        await _apply_queue_snapshot(db, ticket_id, snapshot, status=None)
        return

    snapshot = on_staff_public_reply(queue_line, at=now)
    await _apply_queue_snapshot(
        db,
        ticket_id,
        snapshot,
        status=_staff_reply_workflow_status(str(row.get("status") or "")),
    )


def _format_subscriber_name(name: str | None) -> str:
    """Имя абонента из user_details.name; с заглавной буквы или «Абонент»."""
    raw = (name or "").strip()
    if not raw:
        return "Абонент"
    return raw.capitalize() if len(raw) > 1 else raw.upper()


def _pick_richer_name(*candidates: str | None) -> str:
    """Выбирает наиболее полное непустое имя."""
    best = ""
    best_words = 0
    for raw in candidates:
        name = (raw or "").strip()
        if not name:
            continue
        words = len(name.split())
        if words > best_words or (words == best_words and len(name) > len(best)):
            best = name
            best_words = words
    return best


def _build_subscriber_full_name(
    *,
    person_type: str | None,
    caller_name: str | None,
    is_juridical: int | None,
    surname: str | None,
    name: str | None,
    patronymic: str | None,
    org_short: str | None,
    org_full: str | None,
    user_full_name: str | None,
) -> str:
    """Полное ФИО или название организации (как на карточке абонента)."""
    pt = (person_type or "").strip().lower()
    caller = (caller_name or "").strip()
    if pt == "cs" and caller:
        return caller
    if int(is_juridical or 0) == 2:
        return _pick_richer_name(org_short, org_full, user_full_name)
    fio = " ".join(
        p.strip()
        for p in (surname, name, patronymic)
        if p and str(p).strip()
    ).strip()
    return _pick_richer_name(fio, user_full_name)


_SUBSCRIBER_IDENTITY_SQL = """
    SELECT
        u.is_juridical,
        u.full_name AS user_full_name,
        jcl.short_name_organization AS org_short_name,
        jcl.name_organization AS org_full_name,
        sn.surname AS ud_surname,
        fn.name AS ud_name,
        pn.patronymic AS ud_patronymic
    FROM users."user" u
    LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.juridical_id
    LEFT JOIN LATERAL (
        SELECT NULLIF(TRIM(ud.surname), '') AS surname
        FROM users.user_details ud
        WHERE ud.user_id = u.id
          AND NULLIF(TRIM(ud.surname), '') IS NOT NULL
        ORDER BY ud.is_actual DESC NULLS LAST, ud.id DESC
        LIMIT 1
    ) sn ON TRUE
    LEFT JOIN LATERAL (
        SELECT NULLIF(TRIM(ud.name), '') AS name
        FROM users.user_details ud
        WHERE ud.user_id = u.id
          AND NULLIF(TRIM(ud.name), '') IS NOT NULL
        ORDER BY ud.is_actual DESC NULLS LAST, ud.id DESC
        LIMIT 1
    ) fn ON TRUE
    LEFT JOIN LATERAL (
        SELECT NULLIF(TRIM(ud.patronymic), '') AS patronymic
        FROM users.user_details ud
        WHERE ud.user_id = u.id
          AND NULLIF(TRIM(ud.patronymic), '') IS NOT NULL
        ORDER BY ud.is_actual DESC NULLS LAST, ud.id DESC
        LIMIT 1
    ) pn ON TRUE
    WHERE u.id = :uid
"""


async def fetch_subscriber_identity(
    db: AsyncSession,
    user_id: int | None,
    *,
    person_type: str | None = None,
    caller_name: str | None = None,
) -> dict[str, Any]:
    """Полное имя для сайдбара и короткое (имя) для сообщений."""
    if not user_id:
        caller = (caller_name or "").strip()
        if (person_type or "").strip().lower() == "cs" and caller:
            return {
                "full_name": caller,
                "chat_name": caller,
                "is_juridical": 0,
            }
        return {"full_name": "", "chat_name": "Абонент", "is_juridical": 0}

    row = (
        await db.execute(text(_SUBSCRIBER_IDENTITY_SQL), {"uid": int(user_id)})
    ).mappings().first()
    if not row:
        return {"full_name": "", "chat_name": "Абонент", "is_juridical": 0}

    is_jur = int(row["is_juridical"] or 0)
    full_name = _build_subscriber_full_name(
        person_type=person_type,
        caller_name=caller_name,
        is_juridical=is_jur,
        surname=row.get("ud_surname"),
        name=row.get("ud_name"),
        patronymic=row.get("ud_patronymic"),
        org_short=row.get("org_short_name"),
        org_full=row.get("org_full_name"),
        user_full_name=row.get("user_full_name"),
    )
    chat_name = _format_subscriber_name(row.get("ud_name"))
    if chat_name == "Абонент" and full_name:
        if is_jur == 2:
            chat_name = full_name
        else:
            parts = full_name.split()
            chat_name = _format_subscriber_name(parts[1] if len(parts) >= 2 else parts[0])

    return {
        "full_name": full_name,
        "chat_name": chat_name,
        "is_juridical": is_jur,
    }


async def fetch_subscriber_display_name(
    db: AsyncSession,
    user_id: int | None,
) -> str:
    identity = await fetch_subscriber_identity(db, user_id)
    return str(identity.get("chat_name") or "Абонент")


def _staff_author_role(staff_role: str | None, side: str) -> str | None:
    if side in ("client", "bot", "partner"):
        return None
    role = (staff_role or "").strip().lower()
    return role or None


def _staff_side_and_name(
    *,
    author_id: int | None,
    viewer_id: int,
    full_name: str | None,
    role: str | None,
) -> tuple[str, str]:
    """(side, author_name): me | support | engineer."""
    aid = int(author_id or 0)
    if aid and aid == viewer_id:
        return ("me", "Вы")
    role_l = (role or "").strip().lower()
    name = (full_name or "").strip()
    if role_l == "support":
        return ("support", name or "КЦ")
    return ("engineer", "Инженер")


def _classify_mail_message(
    *,
    viewer_id: int,
    is_bot: bool,
    is_out: bool,
    person_type: str | None,
    author_id: int | None,
    staff_full_name: str | None,
    staff_role: str | None,
    subscriber_name: str = "Абонент",
) -> tuple[str, str]:
    if is_bot:
        return ("bot", "Бот")
    pt = (person_type or "").strip().lower()
    if is_out:
        if pt == "skystream" or pt in STAFF_READ_PERSON_TYPES:
            side, name = _staff_side_and_name(
                author_id=author_id,
                viewer_id=viewer_id,
                full_name=staff_full_name,
                role=staff_role,
            )
            return (side, name)
        return ("me", "КЦ")
    if pt in ("", "user"):
        return ("client", subscriber_name)
    if pt == "skystream" or pt in STAFF_READ_PERSON_TYPES:
        side, name = _staff_side_and_name(
            author_id=author_id,
            viewer_id=viewer_id,
            full_name=staff_full_name,
            role=staff_role,
        )
        return (side, name)
    if pt in ("partner", "tech"):
        return ("partner", "Партнёр")
    return ("client", subscriber_name)


def _classify_tracker_message(
    *,
    viewer_id: int,
    author_id: int,
    person_type: str | None,
    staff_full_name: str | None,
    staff_role: str | None,
    subscriber_name: str = "Абонент",
) -> tuple[str, str]:
    pt = (person_type or "skystream").lower()
    if author_id == viewer_id:
        return ("me", "Вы")
    if pt == "user":
        return ("client", subscriber_name)
    if pt in ("partner", "tech"):
        return ("partner", staff_full_name or "Партнёр")
    if pt == "skystream" or pt in STAFF_READ_PERSON_TYPES:
        return _staff_side_and_name(
            author_id=author_id,
            viewer_id=viewer_id,
            full_name=staff_full_name,
            role=staff_role,
        )
    return ("engineer", "Инженер")


def _sql_staff_read_exists(alias_r: str = "r") -> str:
    return f"{alias_r}.person_type IN ({_STAFF_READ_IN_SQL})"


def ticket_has_unread_sql(tbl: str = _TICKET_TBL) -> str:
    """Коррелированное условие: есть непрочитанные сообщения абонента."""
    mail = f"""
    EXISTS (
        SELECT 1 FROM users.user_mail um
        WHERE (
            um.ticket_id = {tbl}.id
            OR EXISTS (
                SELECT 1 FROM users.tracker_ticket_mail_links l
                WHERE l.ticket_id = {tbl}.id AND l.user_mail_id = um.id
            )
        )
        AND ({_MAIL_IS_CLIENT})
        AND NOT EXISTS (
            SELECT 1 FROM users.user_mail_reads r
            WHERE r.msg_id = um.id AND {_sql_staff_read_exists()}
        )
    )
    """
    tracker = f"""
    EXISTS (
        SELECT 1 FROM users.tracker_messages tm
        WHERE tm.ticket_id = {tbl}.id
          AND COALESCE(tm.person_type, 'skystream') = 'user'
          AND NOT EXISTS (
            SELECT 1 FROM users.tracker_messages_reads r
            WHERE r.msg_id = tm.id AND {_sql_staff_read_exists()}
          )
    )
    """
    return f"""
    (
        COALESCE({tbl}.source, 'call_center') = 'lk' AND ({mail})
    ) OR (
        COALESCE({tbl}.source, 'call_center') <> 'lk' AND ({tracker})
    )
    """


def _sql_mail_unread_min_time(tbl: str = _TICKET_TBL) -> str:
    return f"""
    (SELECT MIN(COALESCE(um.date_tz, to_timestamp(um.date)))
     FROM users.user_mail um
     WHERE (
         um.ticket_id = {tbl}.id
         OR EXISTS (
             SELECT 1 FROM users.tracker_ticket_mail_links l
             WHERE l.ticket_id = {tbl}.id AND l.user_mail_id = um.id
         )
     )
       AND ({_MAIL_IS_CLIENT})
       AND NOT EXISTS (
           SELECT 1 FROM users.user_mail_reads r
           WHERE r.msg_id = um.id AND {_sql_staff_read_exists()}
       ))
    """


def _sql_tracker_unread_min_time(tbl: str = _TICKET_TBL) -> str:
    return f"""
    (SELECT MIN(tm.created_at)
     FROM users.tracker_messages tm
     WHERE tm.ticket_id = {tbl}.id
       AND COALESCE(tm.person_type, 'skystream') = 'user'
       AND NOT EXISTS (
           SELECT 1 FROM users.tracker_messages_reads r
           WHERE r.msg_id = tm.id AND {_sql_staff_read_exists()}
       ))
    """


def ticket_waiting_since_sql(tbl: str = _TICKET_TBL) -> str:
    """Момент, с которого абонент ждёт реакции (ASC = дольше ждёт — выше в списке)."""
    unread = ticket_has_unread_sql(tbl)
    mail_min = _sql_mail_unread_min_time(tbl)
    tracker_min = _sql_tracker_unread_min_time(tbl)
    return f"""
    CASE
        WHEN ({unread}) AND COALESCE({tbl}.source, 'call_center') = 'lk'
            THEN {mail_min}
        WHEN ({unread}) AND COALESCE({tbl}.source, 'call_center') <> 'lk'
            THEN {tracker_min}
        WHEN COALESCE({tbl}.source, 'call_center') = 'lk'
             AND {tbl}.first_response_at IS NULL
            THEN {tbl}.date_of_create
        ELSE COALESCE(
            {tbl}.last_client_message_at,
            {tbl}.updated_at,
            {tbl}.date_of_create
        )
    END
    """


def ticket_list_has_unread_label():
    return literal_column(f"({ticket_has_unread_sql()})", type_=Boolean).label("calc_has_unread")


def _enum_status_sql(statuses: tuple[str, ...]) -> str:
    return ", ".join(f"'{s}'::users.tracker_status" for s in statuses)


def _tracker_list_status_sources_sql(*, closed: bool) -> str:
    statuses = TRACKER_CLOSED_STATUSES if closed else TRACKER_OPEN_STATUSES
    status_in = _enum_status_sql(statuses)
    sources_in = ", ".join(f"'{s}'" for s in TRACKER_HELPDESK_LIST_SOURCES)
    return f"""
        tt.status IN ({status_in})
        AND COALESCE(tt.source, 'call_center') IN ({sources_in})
    """


def _tracker_subscriber_filter_sql(subscriber_q: str | None) -> tuple[str, dict[str, Any]]:
    q = (subscriber_q or "").strip()
    if not q:
        return "", {}
    pattern = f"%{q}%"
    params: dict[str, Any] = {"sub_q_pattern": pattern}
    parts = [
        """EXISTS (
            SELECT 1 FROM users."user" su
            WHERE su.id = tt.user_id AND tt.object_type = 'user'
            AND (
                lower(su.login) LIKE lower(:sub_q_pattern)
                OR cast(su.id as text) LIKE :sub_q_pattern
                OR EXISTS (
                    SELECT 1 FROM users.user_details sud
                    WHERE sud.user_id = su.id AND sud.is_actual IS TRUE
                    AND lower(trim(concat_ws(' ', sud.surname, sud.name, sud.patronymic)))
                        LIKE lower(:sub_q_pattern)
                )
                OR EXISTS (
                    SELECT 1 FROM oss.jur_client_list jcl
                    WHERE jcl.id = su.juridical_id
                    AND lower(jcl.short_name_organization) LIKE lower(:sub_q_pattern)
                )
            )
        )"""
    ]
    if q.isdigit():
        params["sub_q_id"] = int(q)
        parts.insert(0, "tt.user_id = :sub_q_id")
    return f"AND ({' OR '.join(parts)})", params


def _tracker_date_filter_sql(
    *,
    closed: bool,
    date_from: date | None,
    date_to: date | None,
) -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {}
    col = (
        "COALESCE(tt.date_of_close, tt.updated_at, tt.date_of_create)"
        if closed
        else "tt.date_of_create"
    )
    clauses: list[str] = []
    if date_from is not None:
        params["list_date_from"] = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        clauses.append(f"{col} >= :list_date_from")
    if date_to is not None:
        end = datetime.combine(date_to, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        params["list_date_to"] = end
        clauses.append(f"{col} < :list_date_to")
    if not clauses:
        return "", {}
    return f"AND {' AND '.join(clauses)}", params


def _support_co_executor_exists_sql(*, ticket_expr: str, user_param: str) -> str:
    """Участие оператора КС в тикете (общая таблица, фильтр по role=support)."""
    return f"""EXISTS (
        SELECT 1
        FROM users.tracker_ticket_executors e
        JOIN users.skystream_users su ON su.id = e.abs_user_id
        WHERE e.ticket_id = {ticket_expr}
          AND e.abs_user_id = {user_param}
          AND su.role = 'support'
    )"""


def _tracker_assignee_filter_sql(assigned_to: int | None) -> tuple[str, dict[str, Any]]:
    if assigned_to is None:
        return "", {}
    co_exec = _support_co_executor_exists_sql(ticket_expr="tt.id", user_param=":list_assigned_to")
    return f"""AND (
        tt.assigned_to = :list_assigned_to
        OR {co_exec}
    )""", {"list_assigned_to": assigned_to}


def _tracker_list_filter_sql(
    *,
    closed: bool,
    subscriber_q: str | None,
    date_from: date | None,
    date_to: date | None,
    hide_manager_line: bool = False,
    assigned_to: int | None = None,
) -> tuple[str, dict[str, Any]]:
    base = _tracker_list_status_sources_sql(closed=closed)
    sub_sql, sub_params = _tracker_subscriber_filter_sql(subscriber_q)
    date_sql, date_params = _tracker_date_filter_sql(
        closed=closed, date_from=date_from, date_to=date_to
    )
    assignee_sql, assignee_params = _tracker_assignee_filter_sql(assigned_to)
    manager_sql = "AND tt.support_line <> 4" if hide_manager_line else ""
    sql = f"{base}\n          {sub_sql}\n          {date_sql}\n          {manager_sql}\n          {assignee_sql}"
    params = {**sub_params, **date_params, **assignee_params}
    return sql, params


def _mail_client_filter(alias: str = "um") -> str:
    return f"""
    CASE WHEN {alias}.user_id IS NOT NULL AND {alias}.person_type IS NOT NULL
         THEN CASE WHEN {alias}.person_type = 'user' THEN 0 ELSE 1 END
         ELSE COALESCE({alias}.answer, 0) END = 0
    """


def _tracker_list_viewer_owner_sql() -> str:
    """Мои тикеты: основной/соисполнитель КС или инженер на своей линии."""
    co_exec = _support_co_executor_exists_sql(ticket_expr="q.id", user_param=":viewer_id")
    return f"""(
        q.assigned_to = :viewer_id
        OR {co_exec}
        OR (
            q.queue_line = 'engineers'::users.tracker_queue_line
            AND q.engineer_id = :viewer_id
        )
    )"""


def _tracker_list_viewer_line_needs_reply_sql() -> str:
    """Нужен ответ staff на линии тикета или есть непрочитанное."""
    return """(
        q.calc_has_unread
        OR (
            q.chat_turn = 'staff'::users.tracker_chat_turn
            AND (
                (q.queue_line = 'cs'::users.tracker_queue_line
                 AND q.action_by = 'cs'::users.tracker_action_by)
                OR (q.queue_line = 'engineers'::users.tracker_queue_line
                    AND q.action_by = 'engineers'::users.tracker_action_by)
                OR (q.queue_line = 'partner'::users.tracker_queue_line
                    AND q.action_by = 'partner'::users.tracker_action_by)
            )
        )
    )"""


def _tracker_list_staff_needs_reply_sql() -> str:
    """Нужен ответ любой линии staff или есть непрочитанное (без привязки к assigned_to)."""
    return """(
        q.calc_has_unread
        OR (
            q.chat_turn = 'staff'::users.tracker_chat_turn
            AND q.action_by IN (
                'cs'::users.tracker_action_by,
                'engineers'::users.tracker_action_by,
                'partner'::users.tracker_action_by
            )
        )
    )"""


def _tracker_list_cs_unassigned_sql() -> str:
    return """(
        q.queue_line = 'cs'::users.tracker_queue_line
        AND q.assigned_to IS NULL
        AND q.engineer_id IS NULL
    )"""


def _tracker_list_cs_other_assignee_sql() -> str:
    co_exec = _support_co_executor_exists_sql(ticket_expr="q.id", user_param=":viewer_id")
    return f"""(
        q.queue_line = 'cs'::users.tracker_queue_line
        AND q.assigned_to IS NOT NULL
        AND q.assigned_to <> :viewer_id
        AND NOT {co_exec}
    )"""


def _tracker_list_eng_unassigned_sql() -> str:
    return """(
        q.queue_line = 'engineers'::users.tracker_queue_line
        AND q.engineer_id IS NULL
    )"""


def _tracker_list_lk_staff_pending_sql() -> str:
    """ЛК: нужен ответ staff (КС видит даже на линии инженеров)."""
    return """(
        COALESCE(q.source, 'call_center') = 'lk'
        AND q.chat_turn = 'staff'::users.tracker_chat_turn
        AND q.action_by IN (
            'cs'::users.tracker_action_by,
            'engineers'::users.tracker_action_by,
            'partner'::users.tracker_action_by
        )
    )"""


def _tracker_list_sort_tier_sql() -> str:
    """
    Tier 0 — нужен ответ staff / непрочитанное (любая линия, любой исполнитель)
    Tier 1 — мои, без ожидания ответа
    Tier 2 — остальные без ожидания ответа
    Tier 3 — external, операционная пауза
    """
    operational_in = _enum_status_sql(TRACKER_OPERATIONAL_WAIT_STATUSES)
    owner = _tracker_list_viewer_owner_sql()
    needs = _tracker_list_staff_needs_reply_sql()
    return f"""
        CASE
            WHEN q.action_by = 'external'::users.tracker_action_by THEN 3
            WHEN q.status IN ({operational_in}) AND NOT ({needs}) THEN 3
            WHEN {needs} THEN 0
            WHEN {owner} THEN 1
            ELSE 2
        END
    """


def _tracker_list_order_sql(*, closed: bool) -> str:
    if closed:
        return """
        COALESCE(q.date_of_close, q.updated_at, q.date_of_create) DESC NULLS LAST,
        q.id DESC
        """
    sort_tier = _tracker_list_sort_tier_sql()
    return f"""
        {sort_tier},
        CASE
            WHEN q.chat_turn = 'staff'::users.tracker_chat_turn
                THEN EXTRACT(EPOCH FROM COALESCE(q.action_since, q.waiting_since))
            WHEN q.action_by = 'subscriber'::users.tracker_action_by
                THEN -EXTRACT(EPOCH FROM COALESCE(q.action_since, q.updated_at, q.date_of_create))
            ELSE EXTRACT(EPOCH FROM COALESCE(q.action_since, q.waiting_since))
        END,
        CASE q.priority::text
            WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'middle' THEN 2 WHEN 'low' THEN 3 ELSE 4
        END,
        CASE WHEN COALESCE(q.source, 'call_center') = 'lk' AND q.first_response_at IS NULL THEN 0 ELSE 1 END,
        q.id ASC
    """


def _build_tracker_list_queue_ctes_sql(*, filter_sql: str) -> str:
    """CTE filtered → queue для списка /tickets (unread только по id из filtered)."""
    mail_client = _mail_client_filter("um")
    staff = _STAFF_READ_IN_SQL
    return f"""
    WITH filtered AS (
        SELECT tt.id
        FROM users.tracker_tickets tt
        WHERE {filter_sql}
    ),
    mail_msgs AS (
        SELECT f.id AS ticket_id,
               COALESCE(um.date_tz, to_timestamp(um.date)) AS msg_at
        FROM filtered f
        JOIN users.user_mail um ON um.ticket_id = f.id
        WHERE ({mail_client})
          AND NOT EXISTS (
              SELECT 1 FROM users.user_mail_reads r
              WHERE r.msg_id = um.id AND r.person_type IN ({staff})
          )
        UNION ALL
        SELECT f.id,
               COALESCE(um.date_tz, to_timestamp(um.date))
        FROM filtered f
        JOIN users.tracker_ticket_mail_links l ON l.ticket_id = f.id
        JOIN users.user_mail um ON um.id = l.user_mail_id
        WHERE ({mail_client})
          AND NOT EXISTS (
              SELECT 1 FROM users.user_mail_reads r
              WHERE r.msg_id = um.id AND r.person_type IN ({staff})
          )
    ),
    mail_unread AS (
        SELECT ticket_id, MIN(msg_at) AS oldest_unread_at
        FROM mail_msgs
        GROUP BY ticket_id
    ),
    tracker_unread AS (
        SELECT tm.ticket_id, MIN(tm.created_at) AS oldest_unread_at
        FROM users.tracker_messages tm
        JOIN filtered f ON f.id = tm.ticket_id
        WHERE COALESCE(tm.person_type, 'skystream') = 'user'
          AND NOT EXISTS (
              SELECT 1 FROM users.tracker_messages_reads r
              WHERE r.msg_id = tm.id AND r.person_type IN ({staff})
          )
        GROUP BY tm.ticket_id
    ),
    queue AS (
        SELECT
            tt.id,
            tt.title,
            tt.object_type,
            tt.status,
            tt.priority,
            tt.support_line,
            tt.source,
            tt.user_id,
            tt.assigned_to,
            tt.engineer_id,
            tt.category_id,
            tt.date_of_create,
            tt.updated_at,
            tt.date_of_close,
            tt.first_response_at,
            tt.last_client_message_at,
            tt.queue_line,
            tt.action_by,
            tt.chat_turn,
            tt.action_since,
            (COALESCE(tt.source, 'call_center') = 'lk' AND mu.ticket_id IS NOT NULL)
                OR (COALESCE(tt.source, 'call_center') <> 'lk' AND tu.ticket_id IS NOT NULL)
                AS calc_has_unread,
            (tt.chat_turn = 'subscriber'::users.tracker_chat_turn) AS calc_awaiting_subscriber,
            CASE
                WHEN tt.chat_turn = 'staff'::users.tracker_chat_turn
                     AND tt.action_by IN (
                         'cs'::users.tracker_action_by,
                         'engineers'::users.tracker_action_by,
                         'partner'::users.tracker_action_by
                     ) THEN 'needs_reply'
                WHEN tt.chat_turn = 'subscriber'::users.tracker_chat_turn
                     AND COALESCE(tt.source, 'call_center') = 'lk'
                    THEN 'awaiting_subscriber'
                ELSE NULL
            END AS communication_state,
            CASE
                WHEN COALESCE(tt.source, 'call_center') = 'lk' AND mu.ticket_id IS NOT NULL
                    THEN mu.oldest_unread_at
                WHEN COALESCE(tt.source, 'call_center') <> 'lk' AND tu.ticket_id IS NOT NULL
                    THEN tu.oldest_unread_at
                WHEN COALESCE(tt.source, 'call_center') = 'lk' AND tt.first_response_at IS NULL
                    THEN tt.date_of_create
                ELSE COALESCE(tt.last_client_message_at, tt.updated_at, tt.date_of_create)
            END AS waiting_since
        FROM users.tracker_tickets tt
        JOIN filtered f ON f.id = tt.id
        LEFT JOIN mail_unread mu ON mu.ticket_id = tt.id
        LEFT JOIN tracker_unread tu ON tu.ticket_id = tt.id
    )
    """


_LIST_DIGEST_CACHE_TTL = 8


def _tracker_list_digest_cache_key(
    *,
    viewer_id: int,
    closed: bool,
    page: int,
    per_page: int,
    subscriber_q: str | None,
    date_from: date | None,
    date_to: date | None,
    assigned_to: int | None = None,
) -> str:
    payload = json.dumps(
        {
            "v": viewer_id,
            "c": closed,
            "p": page,
            "n": per_page,
            "q": (subscriber_q or "").strip(),
            "df": date_from.isoformat() if date_from else "",
            "dt": date_to.isoformat() if date_to else "",
            "a": assigned_to,
        },
        sort_keys=True,
        ensure_ascii=True,
    )
    h = hashlib.sha256(payload.encode()).hexdigest()[:24]
    return f"tracker_list_digest:{h}"


def _build_tracker_list_digest_sql(*, closed: bool, filter_sql: str) -> str:
    """Лёгкий отпечаток страницы списка (без join абонентов/категорий/исполнителей)."""
    order_by = _tracker_list_order_sql(closed=closed)
    queue_ctes = _build_tracker_list_queue_ctes_sql(filter_sql=filter_sql)
    return f"""
    {queue_ctes},
    page_slice AS (
        SELECT
            q.id,
            q.status::text AS status,
            q.priority::text AS priority,
            q.queue_line::text AS queue_line,
            q.action_by::text AS action_by,
            q.chat_turn::text AS chat_turn,
            q.action_since,
            q.updated_at,
            q.calc_has_unread,
            q.assigned_to,
            q.engineer_id,
            ROW_NUMBER() OVER (ORDER BY {order_by}) AS rn
        FROM queue q
        ORDER BY
            {order_by}
        LIMIT :per_page OFFSET :offset
    )
    SELECT
        (SELECT COUNT(*)::bigint FROM filtered) AS total,
        md5(COALESCE(string_agg(
            concat_ws('|',
                ps.id::text,
                ps.status,
                COALESCE(ps.priority, ''),
                ps.queue_line,
                ps.action_by,
                ps.chat_turn,
                COALESCE(EXTRACT(EPOCH FROM ps.action_since)::bigint::text, ''),
                COALESCE(EXTRACT(EPOCH FROM ps.updated_at)::bigint::text, ''),
                ps.calc_has_unread::text,
                COALESCE(ps.assigned_to::text, ''),
                COALESCE(ps.engineer_id::text, '')
            ),
            ',' ORDER BY ps.rn
        ), '')) AS digest
    FROM page_slice ps
    """


def _build_tracker_list_page_sql(*, closed: bool, filter_sql: str) -> str:
    """Список /tickets: unread по user_mail только для id из filtered (без seq scan на 175k+)."""
    order_by = _tracker_list_order_sql(closed=closed)
    queue_ctes = _build_tracker_list_queue_ctes_sql(filter_sql=filter_sql)
    return f"""
    {queue_ctes}
    SELECT
        q.id,
        q.title,
        q.object_type,
        q.status::text AS status,
        q.priority::text AS priority,
        q.support_line,
        q.source,
        q.user_id,
        q.assigned_to,
        q.engineer_id,
        q.queue_line::text AS queue_line,
        q.action_by::text AS action_by,
        q.chat_turn::text AS chat_turn,
        q.action_since,
        q.date_of_create,
        q.updated_at,
        q.date_of_close,
        q.calc_has_unread,
        q.calc_awaiting_subscriber,
        q.communication_state,
        ttr.rating,
        ttr.comment AS rating_comment,
        u.login AS subscriber_login,
        u.is_juridical AS sub_is_juridical,
        ud.surname AS ud_surname,
        ud.name AS ud_name,
        ud.patronymic AS ud_patronymic,
        jur.short_name_organization AS jur_short_name,
        tc.name AS category_name,
        tcp.name AS category_parent_name,
        cs_op.full_name AS assignee_name,
        cs_op.role AS assignee_role
    FROM queue q
    LEFT JOIN users."user" u ON q.user_id = u.id AND q.object_type = 'user'
    LEFT JOIN LATERAL (
        SELECT ud.surname, ud.name, ud.patronymic
        FROM users.user_details ud
        WHERE ud.user_id = u.id AND ud.is_actual IS TRUE
        ORDER BY ud.id DESC
        LIMIT 1
    ) ud ON TRUE
    LEFT JOIN oss.jur_client_list jur ON jur.id = u.juridical_id
    LEFT JOIN users.ticket_categories tc ON q.category_id = tc.id
    LEFT JOIN users.ticket_categories tcp ON tc.parent_id = tcp.id
    LEFT JOIN users.skystream_users cs_op ON q.assigned_to = cs_op.id
    LEFT JOIN users.tracker_tickets_ratings ttr ON ttr.ticket_id = q.id
    ORDER BY
        {order_by}
    LIMIT :per_page OFFSET :offset
    """


async def fetch_operator_ticket_month_stats(
    db: AsyncSession,
    *,
    user_id: int,
    year: int,
    month: int,
) -> dict[str, int | str]:
    """Открытые (созданные в месяце) и закрытые (закрытые в месяце) тикеты оператора."""
    from calendar import monthrange

    date_from = date(year, month, 1)
    date_to = date(year, month, monthrange(year, month)[1])
    hide_manager = await _viewer_hides_manager_line(db, user_id)

    async def _count(*, closed: bool) -> int:
        filter_sql, filter_params = _tracker_list_filter_sql(
            closed=closed,
            subscriber_q=None,
            date_from=date_from,
            date_to=date_to,
            hide_manager_line=hide_manager,
            assigned_to=user_id,
        )
        row = (
            await db.execute(
                text(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM users.tracker_tickets tt
                    WHERE {filter_sql}
                    """
                ),
                filter_params,
            )
        ).mappings().first()
        return int(row["total"] if row else 0)

    open_count = await _count(closed=False)
    closed_count = await _count(closed=True)
    return {
        "year": year,
        "month": month,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "open_count": open_count,
        "closed_count": closed_count,
    }


async def fetch_tracker_list_page(
    db: AsyncSession,
    *,
    viewer_id: int,
    closed: bool,
    page: int,
    per_page: int,
    subscriber_q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    assigned_to: int | None = None,
) -> tuple[int, list[dict[str, Any]], dict[str, float | None]]:
    hide_manager = await _viewer_hides_manager_line(db, viewer_id)
    filter_sql, filter_params = _tracker_list_filter_sql(
        closed=closed,
        subscriber_q=subscriber_q,
        date_from=date_from,
        date_to=date_to,
        hide_manager_line=hide_manager,
        assigned_to=assigned_to,
    )
    params = {**filter_params, "viewer_id": viewer_id, "per_page": per_page, "offset": (page - 1) * per_page}

    count_row = (
        await db.execute(
            text(
                f"""
                SELECT COUNT(*) AS total
                FROM users.tracker_tickets tt
                WHERE {filter_sql}
                """
            ),
            filter_params,
        )
    ).mappings().first()
    total = int(count_row["total"] if count_row else 0)

    page_sql = _build_tracker_list_page_sql(closed=closed, filter_sql=filter_sql)
    rows = (
        await db.execute(
            text(page_sql),
            params,
        )
    ).mappings().all()

    stats: dict[str, float | None] = {"avg_rating": None, "avg_rating_mine": None}
    if closed:
        rating_row = (
            await db.execute(
                text(
                    f"""
                    SELECT
                        AVG(ttr.rating)::float AS avg_rating,
                        AVG(ttr.rating) FILTER (WHERE tt.assigned_to = :viewer_id)::float AS avg_rating_mine
                    FROM users.tracker_tickets tt
                    JOIN users.tracker_tickets_ratings ttr ON ttr.ticket_id = tt.id
                    WHERE {filter_sql}
                    """
                ),
                params,
            )
        ).mappings().first()
        if rating_row:
            avg = rating_row.get("avg_rating")
            avg_mine = rating_row.get("avg_rating_mine")
            stats["avg_rating"] = round(float(avg), 2) if avg is not None else None
            stats["avg_rating_mine"] = round(float(avg_mine), 2) if avg_mine is not None else None

    dict_rows = [dict(r) for r in rows]
    for row in dict_rows:
        assigned = int(row["assigned_to"]) if row.get("assigned_to") is not None else None
        row.update(
            assignee_display_fields(
                assigned_to=assigned,
                full_name=row.get("assignee_name"),
                role=row.get("assignee_role"),
                viewer_id=viewer_id,
            )
        )

    return total, dict_rows, stats


async def fetch_tracker_list_digest(
    db: AsyncSession,
    *,
    viewer_id: int,
    closed: bool,
    page: int,
    per_page: int,
    subscriber_q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    assigned_to: int | None = None,
    client_digest: str | None = None,
) -> dict[str, Any]:
    """
    Отпечаток страницы списка для поллинга: без join абонентов/категорий.
    client_digest совпадает → changed=false, полный list не нужен.
    """
    cache_key = _tracker_list_digest_cache_key(
        viewer_id=viewer_id,
        closed=closed,
        page=page,
        per_page=per_page,
        subscriber_q=subscriber_q,
        date_from=date_from,
        date_to=date_to,
        assigned_to=assigned_to,
    )
    try:
        cached_raw = await redis_client.get(cache_key)
        if cached_raw:
            cached = json.loads(cached_raw)
            if isinstance(cached, dict) and cached.get("digest"):
                digest = str(cached["digest"])
                total = int(cached.get("total") or 0)
                changed = not client_digest or client_digest != digest
                return {"changed": changed, "digest": digest, "total": total}
    except Exception:
        pass

    hide_manager = await _viewer_hides_manager_line(db, viewer_id)
    filter_sql, filter_params = _tracker_list_filter_sql(
        closed=closed,
        subscriber_q=subscriber_q,
        date_from=date_from,
        date_to=date_to,
        hide_manager_line=hide_manager,
        assigned_to=assigned_to,
    )
    params = {
        **filter_params,
        "viewer_id": viewer_id,
        "per_page": per_page,
        "offset": (page - 1) * per_page,
    }
    digest_sql = _build_tracker_list_digest_sql(closed=closed, filter_sql=filter_sql)
    row = (await db.execute(text(digest_sql), params)).mappings().first()
    total = int(row["total"] if row and row.get("total") is not None else 0)
    digest = str(row["digest"] if row and row.get("digest") is not None else "")

    try:
        await redis_client.setex(
            cache_key,
            _LIST_DIGEST_CACHE_TTL,
            json.dumps({"digest": digest, "total": total}, ensure_ascii=True),
        )
    except Exception:
        pass

    changed = not client_digest or client_digest != digest
    return {"changed": changed, "digest": digest, "total": total}


def ticket_list_order_by(viewer_id: int) -> tuple:
    """
    Очередь 1-й линии: линия 1 → мои → без исполнителя → чужие → непрочитанные →
    ЛК без 1-го ответа → приоритет → не «ожидание» → давность ожидания.
    """
    unread = ticket_has_unread_sql()
    waiting = ticket_waiting_since_sql()
    return (
        case((TrackerTickets.support_line == 1, 0), else_=1),
        case(
            (TrackerTickets.assigned_to == viewer_id, 0),
            (TrackerTickets.assigned_to.is_(None), 1),
            else_=2,
        ),
        text(f"CASE WHEN ({unread}) THEN 0 ELSE 1 END"),
        text(
            f"CASE WHEN COALESCE({_TICKET_TBL}.source, 'call_center') = 'lk'"
            f" AND {_TICKET_TBL}.first_response_at IS NULL THEN 0 ELSE 1 END"
        ),
        case(
            (cast(TrackerTickets.priority, String) == "critical", 0),
            (cast(TrackerTickets.priority, String) == "high", 1),
            (cast(TrackerTickets.priority, String) == "middle", 2),
            (cast(TrackerTickets.priority, String) == "low", 3),
            else_=4,
        ),
        case((TrackerTickets.status.in_(TRACKER_OPERATIONAL_WAIT_STATUSES), 1), else_=0),
        literal_column(waiting, type_=DateTime(timezone=True)).asc().nulls_last(),
        TrackerTickets.id.asc(),
    )
_MOSCOW = ZoneInfo("Europe/Moscow")
_MEDIA_ROOT = os.path.abspath(settings.MEDIA_DIR)
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_ALLOWED_EXT = _IMAGE_EXT | {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"}
_UPLOAD_TOKEN_TTL_SEC = 15 * 60
_MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def chat_mode_for_source(source: str | None) -> str:
    """lk → user_mail; остальные источники (call_center, ks, abs, …) → tracker_messages."""
    return "mail" if (source or "call_center").strip() == "lk" else "tracker"


def is_lk_ticket_source(source: str | None) -> bool:
    return (source or "").strip() == "lk"


async def fetch_tickets_has_unread(
    db: AsyncSession,
    ticket_ids: list[int],
    sources: dict[int, str | None],
) -> set[int]:
    """Тикеты с непрочитанными сообщениями абонента (прочитал любой сотрудник — не непрочитано)."""
    if not ticket_ids:
        return set()
    rows = (
        await db.execute(
            text(
                f"""
                SELECT tt.id
                FROM users.tracker_tickets tt
                WHERE tt.id = ANY(:ticket_ids)
                  AND ({ticket_has_unread_sql('tt')})
                """
            ),
            {"ticket_ids": ticket_ids},
        )
    ).scalars().all()
    return {int(x) for x in rows}


async def count_open_unread_tickets(db: AsyncSession) -> int:
    """Открытые тикеты helpdesk с непрочитанными сообщениями абонента."""
    filter_sql = _tracker_list_status_sources_sql(closed=False)
    unread = ticket_has_unread_sql("tt")
    row = (
        await db.execute(
            text(
                f"""
                SELECT COUNT(*) AS cnt
                FROM users.tracker_tickets tt
                WHERE {filter_sql}
                  AND ({unread})
                """
            ),
        )
    ).mappings().first()
    return int(row["cnt"] if row else 0)


def _moscow_ts() -> int:
    return int(datetime.now(_MOSCOW).timestamp())


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _message_edit_meta(
    *,
    updated_at: datetime | None,
    is_edited_flag: bool | None = None,
) -> dict[str, Any]:
    """is_edited и updated_at_iso для сообщения в чате."""
    edited = bool(is_edited_flag) if is_edited_flag is not None else updated_at is not None
    ua = updated_at if isinstance(updated_at, datetime) else None
    if is_edited_flag is None:
        edited = ua is not None
    return {
        "is_edited": edited,
        "updated_at_iso": _iso(ua) if edited and ua else None,
    }


def _text_snippet(text: str | None, limit: int = 100) -> str:
    raw = (text or "").replace("\n", " ").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1] + "…"


def _parse_reply_to_id(raw: str | int | None) -> int | None:
    if raw is None:
        return None
    try:
        val = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return val if val > 0 else None


def _reply_preview_dict(msg: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(msg["id"]),
        "author_name": msg.get("author_name"),
        "text": _text_snippet(msg.get("text") or ""),
        "is_deleted": False,
    }


def _deleted_reply_preview(reply_id: int) -> dict[str, Any]:
    return {
        "id": reply_id,
        "author_name": None,
        "text": "Сообщение удалено",
        "is_deleted": True,
    }


def enrich_reply_previews(messages: list[dict[str, Any]]) -> None:
    by_id = {int(m["id"]): m for m in messages if int(m.get("id") or 0) > 0}
    for m in messages:
        rid = _parse_reply_to_id(m.get("reply_to_id"))
        if not rid:
            m["reply_preview"] = None
            continue
        ref = by_id.get(rid)
        m["reply_preview"] = _reply_preview_dict(ref) if ref else None


async def fetch_reply_previews_missing(
    db: AsyncSession,
    reply_ids: list[int],
    *,
    chat_mode: str,
    viewer_id: int,
    subscriber_display_name: str,
) -> dict[int, dict[str, Any]]:
    if not reply_ids:
        return {}
    if chat_mode == "mail":
        answer_expr = """
            CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                 THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
                 ELSE um.answer END
        """
        rows = (
            await db.execute(
                text(
                    f"""
                    SELECT um.id AS msg_id, um.id_user_from, um.text AS text_raw, um.person_type,
                        um.user_id, ({answer_expr}) AS answer,
                        su.full_name AS staff_full_name,
                        su.role AS staff_role
                    FROM users.user_mail um
                    LEFT JOIN users.skystream_users su
                        ON um.user_id = su.id AND COALESCE(um.person_type, '') = 'skystream'
                    WHERE um.id = ANY(:ids)
                    """
                ),
                {"ids": reply_ids},
            )
        ).mappings().all()
        out: dict[int, dict[str, Any]] = {}
        for r in rows:
            mid = int(r["msg_id"])
            side, author_name = _classify_mail_message(
                viewer_id=viewer_id,
                is_bot=int(r.get("id_user_from") or 0) == 0,
                is_out=int(r["answer"] or 0) == 1,
                person_type=r.get("person_type"),
                author_id=int(r["user_id"]) if r.get("user_id") is not None else None,
                staff_full_name=r.get("staff_full_name"),
                staff_role=r.get("staff_role"),
                subscriber_name=subscriber_display_name,
            )
            out[mid] = {
                "id": mid,
                "author_name": author_name,
                "text": _text_snippet(r.get("text_raw")),
                "is_deleted": False,
            }
        return out

    rows = (
        await db.execute(
            text(
                """
                SELECT tm.id, tm.body, tm.author_id, tm.person_type,
                    su.full_name AS staff_full_name,
                    su.role AS staff_role
                FROM users.tracker_messages tm
                LEFT JOIN users.skystream_users su ON su.id = tm.author_id
                WHERE tm.id = ANY(:ids)
                """
            ),
            {"ids": reply_ids},
        )
    ).mappings().all()
    out = {}
    for r in rows:
        mid = int(r["id"])
        side, author_name = _classify_tracker_message(
            viewer_id=viewer_id,
            author_id=int(r["author_id"]),
            person_type=r.get("person_type"),
            staff_full_name=r.get("staff_full_name"),
            staff_role=r.get("staff_role"),
            subscriber_name=subscriber_display_name,
        )
        out[mid] = {
            "id": mid,
            "author_name": author_name,
            "text": _text_snippet(r.get("body")),
            "is_deleted": False,
        }
    return out


async def attach_reply_previews(
    db: AsyncSession,
    messages: list[dict[str, Any]],
    *,
    chat_mode: str,
    viewer_id: int,
    subscriber_display_name: str,
) -> None:
    enrich_reply_previews(messages)
    missing: list[int] = []
    for m in messages:
        rid = _parse_reply_to_id(m.get("reply_to_id"))
        if rid and not m.get("reply_preview"):
            missing.append(rid)
    if not missing:
        return
    fetched = await fetch_reply_previews_missing(
        db,
        list(set(missing)),
        chat_mode=chat_mode,
        viewer_id=viewer_id,
        subscriber_display_name=subscriber_display_name,
    )
    for m in messages:
        rid = _parse_reply_to_id(m.get("reply_to_id"))
        if not rid or m.get("reply_preview"):
            continue
        if rid in fetched:
            m["reply_preview"] = fetched[rid]
        else:
            m["reply_preview"] = _deleted_reply_preview(rid)


async def _assert_own_mail_message(
    db: AsyncSession,
    ticket_id: int,
    message_id: int,
    operator_id: int,
) -> None:
    row = (
        await db.execute(
            text(
                """
                SELECT 1 FROM users.user_mail um
                WHERE um.id = :mid AND um.ticket_id = :tid
                  AND um.user_id = :op_id
                  AND COALESCE(um.person_type, 'skystream') = 'skystream'
                  AND (
                    CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
                         THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
                         ELSE um.answer END
                  ) = 1
                LIMIT 1
                """
            ),
            {"mid": message_id, "tid": ticket_id, "op_id": operator_id},
        )
    ).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено или нельзя изменить")


async def _assert_own_tracker_message(
    db: AsyncSession,
    ticket_id: int,
    message_id: int,
    operator_id: int,
) -> None:
    row = (
        await db.execute(
            text(
                """
                SELECT 1 FROM users.tracker_messages tm
                WHERE tm.id = :mid AND tm.ticket_id = :tid
                  AND tm.author_id = :op_id
                  AND COALESCE(tm.person_type, 'skystream') = 'skystream'
                LIMIT 1
                """
            ),
            {"mid": message_id, "tid": ticket_id, "op_id": operator_id},
        )
    ).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Сообщение не найдено или нельзя изменить")


async def _assert_reply_target(
    db: AsyncSession,
    ticket_id: int,
    reply_to_id: int | None,
    *,
    chat_mode: str,
) -> None:
    if not reply_to_id:
        return
    if chat_mode == "mail":
        ok = (
            await db.execute(
                text(
                    "SELECT 1 FROM users.user_mail WHERE id = :rid AND ticket_id = :tid LIMIT 1"
                ),
                {"rid": reply_to_id, "tid": ticket_id},
            )
        ).scalar()
    else:
        ok = (
            await db.execute(
                text(
                    """
                    SELECT 1 FROM users.tracker_messages
                    WHERE id = :rid AND ticket_id = :tid LIMIT 1
                    """
                ),
                {"rid": reply_to_id, "tid": ticket_id},
            )
        ).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="Сообщение для ответа не найдено в этом тикете")


def _reader_display_label(
    person_type: str | None,
    role: str | None,
    staff_name: str | None,
) -> str:
    pt = (person_type or "").strip().lower()
    if pt == "user":
        return "Абонент"
    role_l = (role or "").strip().lower()
    if pt == "skystream":
        if role_l == "engineer":
            return "Инженер"
        if role_l == "support":
            return (staff_name or "").strip() or "КЦ"
        name = (staff_name or "").strip()
        if name:
            return name
        return "Сотрудник"
    if pt in ("partner", "tech"):
        return "Партнёр"
    return (staff_name or "").strip() or pt or "—"


def _reader_sort_key(person_type: str | None, role: str | None) -> int:
    pt = (person_type or "").strip().lower()
    role_l = (role or "").strip().lower()
    if pt == "user":
        return 0
    if pt == "skystream" and role_l == "engineer":
        return 1
    if pt == "skystream" and role_l == "support":
        return 2
    return 3


def _build_outbound_read_details(
    rows: list[Any],
    *,
    legacy_read_time: dict[int, datetime] | None = None,
) -> tuple[dict[int, str], dict[int, list[dict[str, str]]]]:
    """Собирает min read time и до 5 читателей на исходящее сообщение."""
    grouped: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        mid = int(r["msg_id"])
        rt = r.get("read_time")
        if not isinstance(rt, datetime):
            continue
        grouped.setdefault(mid, []).append(
            {
                "read_time": rt,
                "person_type": r.get("person_type"),
                "role": r.get("skystream_role"),
                "staff_name": r.get("skystream_name"),
            }
        )

    if legacy_read_time:
        for mid, rt in legacy_read_time.items():
            if mid not in grouped and isinstance(rt, datetime):
                grouped[mid] = [
                    {
                        "read_time": rt,
                        "person_type": "user",
                        "role": None,
                        "staff_name": None,
                    }
                ]

    receipts: dict[int, str] = {}
    read_by: dict[int, list[dict[str, str]]] = {}
    for mid, readers in grouped.items():
        readers.sort(
            key=lambda x: (
                _reader_sort_key(x.get("person_type"), x.get("role")),
                x["read_time"],
            )
        )
        earliest = readers[0]["read_time"]
        receipts[mid] = _iso(earliest) or ""
        read_by[mid] = [
            {
                "label": _reader_display_label(
                    r.get("person_type"),
                    r.get("role"),
                    r.get("staff_name"),
                ),
                "read_at_iso": _iso(r["read_time"]) or "",
            }
            for r in readers[:5]
            if isinstance(r.get("read_time"), datetime)
        ]
    return receipts, read_by


async def load_mail_subscriber_read_receipts(
    db: AsyncSession,
    ticket_id: int,
) -> tuple[dict[int, str], dict[int, list[dict[str, str]]]]:
    """ЛК: прочтение исходящих оператором сообщений абонентом (user_mail_reads.person_type=user)."""
    rows = (
        await db.execute(
            text(
                f"""
                SELECT um.id AS msg_id, r.read_time, r.person_type,
                    NULL::text AS skystream_role,
                    NULL::text AS skystream_name
                FROM users.user_mail um
                INNER JOIN users.user_mail_reads r ON r.msg_id = um.id
                WHERE um.ticket_id = :ticket_id
                  AND NOT ({_MAIL_IS_CLIENT})
                  AND r.person_type = 'user'
                UNION ALL
                SELECT um.id AS msg_id, um.date_tz AS read_time, 'user' AS person_type,
                    NULL::text AS skystream_role,
                    NULL::text AS skystream_name
                FROM users.user_mail um
                WHERE um.ticket_id = :ticket_id
                  AND NOT ({_MAIL_IS_CLIENT})
                  AND um.read::text IN ('1', 't', 'true')
                  AND um.date_tz IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM users.user_mail_reads r2
                      WHERE r2.msg_id = um.id AND r2.person_type = 'user'
                  )
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().all()
    return _build_outbound_read_details(rows)


async def load_tracker_outbound_read_receipts(
    db: AsyncSession,
    ticket_id: int,
) -> tuple[dict[int, str], dict[int, list[dict[str, str]]]]:
    """call_center и др.: прочтение исходящих skystream-сообщений (tracker_messages_reads)."""
    rows = (
        await db.execute(
            text(
                """
                SELECT tm.id AS msg_id, r.read_time, r.person_type,
                    su.role AS skystream_role,
                    su.full_name AS skystream_name
                FROM users.tracker_messages tm
                INNER JOIN users.tracker_messages_reads r ON r.msg_id = tm.id
                LEFT JOIN users.skystream_users su
                    ON r.person_type = 'skystream' AND su.id = r.user_id
                WHERE tm.ticket_id = :ticket_id
                  AND COALESCE(tm.person_type, 'skystream') = 'skystream'
                ORDER BY tm.id, r.read_time ASC
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().all()
    return _build_outbound_read_details(rows)


def _attach_read_receipts(
    messages: list[dict[str, Any]],
    receipts: dict[int, str],
    read_by: dict[int, list[dict[str, str]]],
) -> None:
    for m in messages:
        if m.get("side") in STAFF_OUTBOUND_SIDES:
            mid = int(m["id"])
            m["recipient_read_at_iso"] = receipts.get(mid)
            m["read_by"] = read_by.get(mid, [])
        else:
            m["recipient_read_at_iso"] = None
            m["read_by"] = []


def _media_url(file_path: str | None) -> str | None:
    if not file_path or file_path in ("0", ""):
        return None
    p = file_path.strip()
    if p.startswith("/media/"):
        return p
    if p.startswith("media/"):
        return "/" + p
    return f"/media/{p.lstrip('/')}"


def catalog_source_for_ticket(ticket_source: str | None) -> str:
    """Источник строк в ticket_categories (как в legacy helpdesk)."""
    s = (ticket_source or "call_center").strip()
    if s in ("partner", "tech"):
        return "partner"
    if s == "call_center":
        return "lk"
    return s


async def load_ticket_categories(
    db: AsyncSession,
    *,
    catalog_source: str,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, parent_id, name, slug, theme::text AS theme,
                    complexity, priority::text AS priority, support_line,
                    sla_minutes, sort_order,
                    COALESCE(need_user_selection, false) AS need_user_selection,
                    COALESCE(need_station_selection, false) AS need_station_selection,
                    object_type
                FROM users.ticket_categories
                WHERE is_active = true AND source = :src
                ORDER BY sort_order ASC, name ASC, id ASC
                """
            ),
            {"src": catalog_source},
        )
    ).mappings().all()

    if not rows:
        return []

    nodes: dict[int, dict[str, Any]] = {}
    for r in rows:
        rid = int(r["id"])
        pid = int(r["parent_id"]) if r.get("parent_id") is not None else None
        pr = r.get("priority") or "middle"
        sort_order = int(r.get("sort_order") or 0)
        base = {
            "id": rid,
            "name": r["name"],
            "slug": r["slug"],
            "sort_order": sort_order,
            "parent_id": pid,
        }
        if pid is None:
            nodes[rid] = {**base, "children": []}
        else:
            nodes[rid] = {
                **base,
                "theme": r["theme"],
                "complexity": r["complexity"],
                "priority": pr,
                "priority_label": PRIORITY_DICT.get(pr, pr),
                "support_line": int(r["support_line"]),
                "sla_minutes": int(r["sla_minutes"]),
                "need_user_selection": bool(r.get("need_user_selection")),
                "need_station_selection": bool(r.get("need_station_selection")),
                "object_type": r.get("object_type"),
            }

    roots: list[dict[str, Any]] = []
    for r in rows:
        rid = int(r["id"])
        pid = int(r["parent_id"]) if r.get("parent_id") is not None else None
        node = nodes[rid]
        if pid is None:
            roots.append(node)
        elif pid in nodes and "children" in nodes[pid]:
            nodes[pid]["children"].append(node)

    for root in roots:
        root["children"].sort(key=lambda c: (c["sort_order"], c["name"]))
        for child in root["children"]:
            child.pop("sort_order", None)
            child.pop("parent_id", None)
    roots.sort(key=lambda g: (g["sort_order"], g["name"]))
    for root in roots:
        root.pop("sort_order", None)
        root.pop("parent_id", None)
    return roots


async def load_helpdesk_macros(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, name, message_text, sort_order
                FROM users.helpdesk_macros
                ORDER BY sort_order ASC, id ASC
                """
            )
        )
    ).mappings().all()
    return [
        {
            "id": int(r["id"]),
            "name": str(r["name"]),
            "message_text": str(r["message_text"] or ""),
            "sort_order": int(r["sort_order"] or 0),
        }
        for r in rows
    ]


def _queue_line_display_label(queue_line: str, support_line: int) -> str:
    """Подпись линии из v2 queue_line; support_line=4 → «Менеджер»."""
    if support_line == 4 and queue_line == "cs":
        return SUPPORT_LINE_DISPLAY[4]
    return TRACKER_QUEUE_LINE_DISPLAY.get(queue_line, queue_line)


async def _ticket_detail_has_unread(db: AsyncSession, ticket_id: int) -> bool:
    row = (
        await db.execute(
            text(
                f"""
                SELECT ({ticket_has_unread_sql('tt')}) AS has_unread
                FROM users.tracker_tickets tt
                WHERE tt.id = :ticket_id
                """
            ),
            {"ticket_id": ticket_id},
        )
    ).mappings().first()
    return bool(row and row.get("has_unread"))


async def _viewer_role(db: AsyncSession, viewer_id: int) -> str:
    row = (
        await db.execute(
            text("SELECT role FROM users.skystream_users WHERE id = :id"),
            {"id": viewer_id},
        )
    ).mappings().first()
    return str(row["role"] if row and row.get("role") else "support")


async def _viewer_hides_manager_line(db: AsyncSession, viewer_id: int) -> bool:
    """Операторы КС (role=support) не видят очередь менеджера (support_line=4)."""
    return (await _viewer_role(db, viewer_id)).strip().lower() == "support"


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
                    tt.category_id, tt.assigned_to, tt.engineer_id, tt.author,
                    tt.queue_line::text AS queue_line,
                    tt.action_by::text AS action_by,
                    tt.chat_turn::text AS chat_turn,
                    tt.action_since,
                    COALESCE(tt.priority::text, tc.priority::text) AS priority,
                    tc.name AS category_name,
                    tc.parent_id AS category_parent_id,
                    tcp.name AS category_parent_name,
                    u.login AS subscriber_login,
                    u.is_juridical,
                    COALESCE(
                        EXISTS (
                            SELECT 1
                            FROM radius.radacct r
                            WHERE lower(r.username) = lower(u.login)
                              AND r.acctstoptime IS NULL
                            LIMIT 1
                        ),
                        false
                    ) AS subscriber_online,
                    su.full_name AS assignee_name,
                    su.role AS assignee_role,
                    sf.station_name,
                    ig.name AS station_fallback_name
                FROM users.tracker_tickets tt
                LEFT JOIN users.ticket_categories tc ON tc.id = tt.category_id
                LEFT JOIN users.ticket_categories tcp ON tcp.id = tc.parent_id
                LEFT JOIN users."user" u ON u.id = tt.user_id
                    AND COALESCE(tt.object_type, 'user') = 'user'
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

    viewer_role = await _viewer_role(db, viewer_id)
    if viewer_role == "support" and not is_visible_to_cs_support(line):
        raise HTTPException(status_code=404, detail="Тикет не найден")
    queue_line = _coerce_queue_line(d)
    action_by = str(d.get("action_by") or queue_line)
    chat_turn = _coerce_chat_turn(d)
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
    sub_login = (d.get("subscriber_login") or "").strip()
    uid = int(d["user_id"]) if d.get("user_id") is not None else None
    identity = await fetch_subscriber_identity(
        db,
        uid,
        person_type=d.get("person_type"),
        caller_name=d.get("caller_name"),
    )
    sub_name = (identity.get("full_name") or "").strip()
    subscriber_display_name = str(identity.get("chat_name") or "Абонент")
    sub_is_juridical = int(identity.get("is_juridical") or d.get("is_juridical") or 0)
    if not sub_name and uid:
        sub_name = sub_login or f"Абонент #{uid}"
    if not sub_name and d.get("caller_name"):
        sub_name = str(d["caller_name"]).strip()

    subscriber_account = None
    if uid:
        try:
            subscriber_account = await profile_svc.load_subscriber_account_summary(db, uid)
        except HTTPException:
            subscriber_account = None

    chat_mode = chat_mode_for_source(source)
    date_of_close = d.get("date_of_close")
    can_reopen = ticket_can_reopen(status_raw, date_of_close)

    if status_raw in TRACKER_OPEN_STATUSES:
        await reconcile_ticket_queue_from_thread(db, ticket_id, source=source)
        qrow = await _load_ticket_queue_row(db, ticket_id)
        queue_line = _coerce_queue_line(qrow)
        action_by = str(qrow.get("action_by") or queue_line)
        chat_turn = _coerce_chat_turn(qrow)
        line = int(qrow.get("support_line") or d.get("support_line") or 1)
        status_raw = str(qrow.get("status") or status_raw)
        d["action_since"] = qrow.get("action_since")

    owner_id = int(d["assigned_to"]) if d.get("assigned_to") is not None else None
    assignee_disp = assignee_display_fields(
        assigned_to=owner_id,
        full_name=d.get("assignee_name"),
        role=d.get("assignee_role"),
        viewer_id=viewer_id,
    )
    executor_map = await _fetch_ticket_executor_rows_by_ticket_ids(db, [ticket_id])
    staff_participants = build_ticket_staff_participants(
        assigned_to=owner_id,
        assignee_name=d.get("assignee_name"),
        assignee_role=d.get("assignee_role"),
        executor_rows=executor_map.get(ticket_id, []),
        viewer_id=viewer_id,
    )
    assignee_disp["assignee_is_viewer"] = any(p["is_viewer"] for p in staff_participants)

    has_unread = await _ticket_detail_has_unread(db, ticket_id)
    queue_snap = {
        "queue_line": queue_line,
        "action_by": action_by,
        "chat_turn": chat_turn,
        "action_since": d.get("action_since"),
    }
    list_highlight = list_highlight_for_viewer(
        queue_snap,
        viewer_role=viewer_role,  # type: ignore[arg-type]
        has_unread=has_unread,
        workflow_status=status_raw,
        source=source,
        support_line=line,
    )
    comm_state = communication_state_from_v2(chat_turn, action_by, source=source)
    if comm_state is None and list_highlight == "ops":
        comm_label = STATUS_DISPLAY.get(status_raw, status_raw)
    else:
        comm_label = COMMUNICATION_STATE_LABELS.get(comm_state) if comm_state else None

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
        "support_line_label": SUPPORT_LINE_DISPLAY.get(line, str(line)),
        "queue_line": queue_line,
        "queue_line_label": _queue_line_display_label(queue_line, line),
        "action_by": action_by,
        "action_by_label": TRACKER_ACTION_BY_DISPLAY.get(action_by, action_by),
        "chat_turn": chat_turn,
        "chat_turn_label": TRACKER_CHAT_TURN_DISPLAY.get(chat_turn, chat_turn),
        "action_since_iso": _iso(d.get("action_since")),
        "has_unread": has_unread,
        "list_highlight": list_highlight,
        "communication_state": comm_state,
        "communication_label": comm_label,
        "source": source,
        "source_label": SOURCE_DISPLAY.get(source, source),
        "category_label": category_label,
        "category_name": cat or None,
        "category_parent_name": cat_parent or None,
        "category_id": int(d["category_id"]) if d.get("category_id") is not None else None,
        "category_parent_id": int(d["category_parent_id"])
        if d.get("category_parent_id") is not None
        else None,
        "user_id": int(d["user_id"]) if d.get("user_id") is not None else None,
        "caller_name": d.get("caller_name"),
        "subscriber_name": sub_name or None,
        "subscriber_display_name": subscriber_display_name,
        "subscriber_login": sub_login or None,
        "subscriber_online": bool(d.get("subscriber_online")),
        "subscriber_is_juridical": sub_is_juridical,
        "subscriber_profile_user_id": int(d["user_id"]) if d.get("user_id") is not None else None,
        "assignee_label": assignee_disp["assignee_label"],
        "assignee_role": assignee_disp["assignee_role"],
        "assignee_is_viewer": assignee_disp["assignee_is_viewer"],
        "assigned_to": assignee_disp["assigned_to"],
        "staff_participants": staff_participants,
        "station_name": station,
        "station_id": int(d["station_id"]) if d.get("station_id") else None,
        "date_of_create": d["date_of_create"],
        "date_of_create_iso": _iso(d.get("date_of_create")),
        "date_of_close_iso": _iso(date_of_close),
        "can_reopen": can_reopen,
        "updated_at": d.get("updated_at"),
        "updated_at_iso": _iso(d.get("updated_at")),
        "assigned_at_iso": _iso(assigned_at_row["start_time"]) if assigned_at_row else None,
        "chat_mode": chat_mode,
        "can_reply": status_raw in TRACKER_OPEN_STATUSES
        and (chat_mode == "tracker" or d.get("user_id") is not None),
        "subscriber_account": subscriber_account,
    }


async def link_ticket_subscriber(
    db: AsyncSession,
    ticket_id: int,
    user_id: int,
    viewer_id: int,
) -> dict[str, Any]:
    """Привязать абонента к тикету без user_id (object_type=user, person_type=user)."""
    exists = (
        await db.execute(
            text('SELECT id FROM users."user" WHERE id = :uid'),
            {"uid": user_id},
        )
    ).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="Абонент не найден")

    row = (
        await db.execute(
            text("SELECT id, user_id FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if row.get("user_id") is not None:
        raise HTTPException(status_code=400, detail="Абонент уже привязан к тикету")

    now = datetime.now(timezone.utc)
    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET user_id = :uid,
                object_type = 'user',
                person_type = 'user',
                caller_name = NULL,
                updated_at = :now
            WHERE id = :ticket_id
            """
        ),
        {"uid": user_id, "now": now, "ticket_id": ticket_id},
    )
    await db.commit()
    return await load_ticket_detail(db, ticket_id, viewer_id)


async def _close_active_line_segment(
    db: AsyncSession,
    ticket_id: int,
    now: datetime,
) -> None:
    await db.execute(
        text(
            """
            UPDATE users.tracker_ticket_line_history
            SET end_time = :now
            WHERE id = (
                SELECT id FROM users.tracker_ticket_line_history
                WHERE ticket_id = :ticket_id
                  AND support_line IS NOT NULL
                  AND end_time IS NULL
                ORDER BY id DESC
                LIMIT 1
            )
            """
        ),
        {"ticket_id": ticket_id, "now": now},
    )


def _add_line_history_event(
    db: AsyncSession,
    *,
    ticket_id: int,
    changed_by: int,
    now: datetime,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    db.add(
        TrackerTicketLineHistory(
            ticket_id=ticket_id,
            support_line=None,
            start_time=now,
            changed_by=changed_by,
            event_type=event_type,
            payload=payload,
        )
    )


def _open_line_segment(
    db: AsyncSession,
    *,
    ticket_id: int,
    support_line: int,
    changed_by: int,
    now: datetime,
) -> None:
    db.add(
        TrackerTicketLineHistory(
            ticket_id=ticket_id,
            support_line=support_line,
            start_time=now,
            changed_by=changed_by,
            state="active",
        )
    )


async def _change_ticket_support_line(
    db: AsyncSession,
    *,
    ticket_id: int,
    from_line: int,
    to_line: int,
    changed_by: int,
    now: datetime,
) -> None:
    await _close_active_line_segment(db, ticket_id, now)
    _open_line_segment(
        db,
        ticket_id=ticket_id,
        support_line=to_line,
        changed_by=changed_by,
        now=now,
    )
    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=changed_by,
        now=now,
        event_type="line_changed",
        payload={"from_line": from_line, "to_line": to_line},
    )


async def _record_ticket_closed_history(
    db: AsyncSession,
    *,
    ticket_id: int,
    changed_by: int,
    now: datetime,
    from_status: str,
    to_status: str = "closed",
) -> None:
    """Закрытие: завершить активный сегмент линии + события closed и status_changed."""
    await _close_active_line_segment(db, ticket_id, now)
    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=changed_by,
        now=now,
        event_type="closed",
        payload={"status": to_status, "from_status": from_status},
    )
    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=changed_by,
        now=now,
        event_type="status_changed",
        payload={
            "from_status": from_status,
            "status": to_status,
            "trigger": "close",
        },
    )
    await db.flush()


async def _record_ticket_reopened_history(
    db: AsyncSession,
    *,
    ticket_id: int,
    changed_by: int,
    now: datetime,
    from_status: str,
    to_status: str,
    support_line: int,
) -> None:
    """Переоткрытие: новый сегмент линии + события reopened и status_changed."""
    _open_line_segment(
        db,
        ticket_id=ticket_id,
        support_line=support_line,
        changed_by=changed_by,
        now=now,
    )
    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=changed_by,
        now=now,
        event_type="reopened",
        payload={"from_status": from_status, "status": to_status},
    )
    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=changed_by,
        now=now,
        event_type="status_changed",
        payload={
            "from_status": from_status,
            "status": to_status,
            "trigger": "reopen",
        },
    )
    await db.flush()


async def _validate_leaf_category(
    db: AsyncSession,
    *,
    category_id: int,
    catalog_source: str,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                """
                SELECT id, parent_id, name
                FROM users.ticket_categories
                WHERE id = :cid
                  AND is_active = true
                  AND source = :src
                  AND parent_id IS NOT NULL
                """
            ),
            {"cid": category_id, "src": catalog_source},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=400, detail="Некорректная категория для этого тикета")
    return dict(row)


async def _load_ticket_row_for_line_ops(db: AsyncSession, ticket_id: int) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                """
                SELECT id, support_line, status::text AS status, source, category_id,
                       queue_line::text AS queue_line,
                       chat_turn::text AS chat_turn,
                       action_by::text AS action_by
                FROM users.tracker_tickets
                WHERE id = :id
                """
            ),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    status = str(row["status"] or "")
    if status in TRACKER_CLOSED_STATUSES:
        raise HTTPException(status_code=400, detail="Тикет уже закрыт")
    return dict(row)


TICKET_REOPEN_WINDOW = timedelta(hours=24)


def _coerce_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ticket_can_reopen(status: str | None, date_of_close: datetime | None, *, now: datetime | None = None) -> bool:
    """Переоткрытие доступно в течение 24 ч после date_of_close."""
    status_raw = (status or "").strip()
    if status_raw not in TRACKER_CLOSED_STATUSES:
        return False
    if not date_of_close:
        return False
    ref = now or datetime.now(timezone.utc)
    return ref - _coerce_utc(date_of_close) <= TICKET_REOPEN_WINDOW


async def _assert_ticket_open_for_write(db: AsyncSession, ticket_id: int) -> None:
    status = (
        await db.execute(
            text("SELECT status::text FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).scalar()
    if not status:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    if str(status) in TRACKER_CLOSED_STATUSES:
        raise HTTPException(status_code=400, detail="Тикет закрыт")


async def register_ticket_co_executor(
    db: AsyncSession,
    ticket_id: int,
    operator_id: int,
) -> None:
    """Зафиксировать участие оператора КС в переписке по тикету."""
    await db.execute(
        text(
            """
            INSERT INTO users.tracker_ticket_executors (ticket_id, abs_user_id)
            VALUES (:ticket_id, :operator_id)
            ON CONFLICT (ticket_id, abs_user_id) DO NOTHING
            """
        ),
        {"ticket_id": ticket_id, "operator_id": operator_id},
    )


def assignee_display_fields(
    *,
    assigned_to: int | None,
    full_name: str | None,
    role: str | None,
    viewer_id: int,
) -> dict[str, Any]:
    """Колонка «Исполнитель»: только assigned_to; ФИО — только для role=support."""
    if assigned_to is None:
        return {
            "assigned_to": None,
            "assignee_label": None,
            "assignee_role": None,
            "assignee_is_viewer": False,
        }
    uid = int(assigned_to)
    is_viewer = uid == viewer_id
    role_l = (role or "support").strip().lower()
    if is_viewer:
        label = "Вы"
    elif role_l == "engineer":
        label = "Инженер"
    elif role_l == "manager":
        label = "Менеджер"
    else:
        label = (full_name or "").strip() or f"#{uid}"
    return {
        "assigned_to": uid,
        "assignee_label": label,
        "assignee_role": role_l,
        "assignee_is_viewer": is_viewer,
    }


def _staff_participant_label(
    uid: int,
    full_name: str | None,
    role: str | None,
    viewer_id: int,
) -> str:
    if uid == viewer_id:
        return "Вы"
    role_l = (role or "support").strip().lower()
    if role_l == "engineer":
        return "Инженер"
    if role_l == "manager":
        return "Менеджер"
    return (full_name or "").strip() or f"#{uid}"


def build_ticket_staff_participants(
    *,
    assigned_to: int | None,
    assignee_name: str | None,
    assignee_role: str | None,
    executor_rows: list[dict[str, Any]],
    viewer_id: int,
) -> list[dict[str, Any]]:
    """assigned_to (основной) + соисполнители support из tracker_ticket_executors."""
    out: list[dict[str, Any]] = []
    seen: set[int] = set()

    def _append(
        uid: int,
        name: str | None,
        role: str | None,
        *,
        is_primary: bool,
    ) -> None:
        if uid in seen:
            return
        seen.add(uid)
        role_l = (role or "support").strip().lower()
        out.append(
            {
                "id": uid,
                "label": _staff_participant_label(uid, name, role_l, viewer_id),
                "role": role_l,
                "is_primary": is_primary,
                "is_viewer": uid == viewer_id,
            }
        )

    if assigned_to is not None:
        _append(int(assigned_to), assignee_name, assignee_role, is_primary=True)

    for row in executor_rows:
        uid = int(row["abs_user_id"])
        if uid in seen:
            continue
        role_l = (row.get("role") or "support").strip().lower()
        if role_l != "support":
            continue
        _append(uid, row.get("full_name"), role_l, is_primary=False)

    return out


async def _fetch_ticket_executor_rows_by_ticket_ids(
    db: AsyncSession,
    ticket_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    if not ticket_ids:
        return {}
    rows = (
        await db.execute(
            text(
                """
                SELECT e.ticket_id, e.abs_user_id, su.full_name, su.role, e.created_at
                FROM users.tracker_ticket_executors e
                JOIN users.skystream_users su ON su.id = e.abs_user_id
                WHERE e.ticket_id = ANY(:ids)
                  AND su.role = 'support'
                ORDER BY e.ticket_id, e.created_at, e.abs_user_id
                """
            ),
            {"ids": ticket_ids},
        )
    ).mappings().all()
    grouped: dict[int, list[dict[str, Any]]] = {tid: [] for tid in ticket_ids}
    for row in rows:
        tid = int(row["ticket_id"])
        grouped.setdefault(tid, []).append(dict(row))
    return grouped


async def _maybe_claim_cs_assignee(
    db: AsyncSession,
    ticket_id: int,
    operator_id: int,
    operator_role: str | None,
) -> None:
    """Сообщение оператора КС: соисполнитель в таблице; assigned_to — при первом ответе."""
    if (operator_role or "").strip().lower() != "support":
        return
    await register_ticket_co_executor(db, ticket_id, operator_id)
    row = (
        await db.execute(
            text("SELECT assigned_to FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not row or row.get("assigned_to") is not None:
        return
    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET assigned_to = :operator_id, updated_at = NOW()
            WHERE id = :ticket_id AND assigned_to IS NULL
            """
        ),
        {"operator_id": operator_id, "ticket_id": ticket_id},
    )


async def transfer_ticket_to_engineers(
    db: AsyncSession,
    ticket_id: int,
    category_id: int | None,
    comment: str | None,
    author_id: int,
) -> dict[str, Any]:
    """Передача тикета на линию инженеров: v2 + support_line=2, снятие исполнителей КС."""
    row = await _load_ticket_row_for_line_ops(db, ticket_id)
    await reconcile_ticket_queue_from_thread(db, ticket_id, source=row.get("source"))
    row = await _load_ticket_row_for_line_ops(db, ticket_id)
    from_line = int(row["support_line"] or 1)
    if from_line == 4:
        raise HTTPException(
            status_code=400,
            detail="Тикет на линии менеджера — передача инженерам недоступна",
        )
    if _coerce_queue_line(row) != "cs":
        raise HTTPException(status_code=400, detail="Тикет не на линии КС")

    if category_id is not None:
        catalog = catalog_source_for_ticket(row.get("source"))
        await _validate_leaf_category(db, category_id=category_id, catalog_source=catalog)

    now = datetime.now(timezone.utc)
    old_category_id = row.get("category_id")
    new_category_id = int(category_id) if category_id is not None else None
    queue_snap = on_escalate_to_engineers(
        chat_turn=_coerce_chat_turn(row),
        action_by=str(row.get("action_by") or "engineers"),
        at=now,
    )

    if new_category_id is not None:
        await db.execute(
            text(
                """
                UPDATE users.tracker_tickets
                SET category_id = :category_id,
                    engineer_id = NULL,
                    updated_at = :now
                WHERE id = :ticket_id
                """
            ),
            {"category_id": new_category_id, "now": now, "ticket_id": ticket_id},
        )
    else:
        await db.execute(
            text(
                """
                UPDATE users.tracker_tickets
                SET engineer_id = NULL,
                    updated_at = :now
                WHERE id = :ticket_id
                """
            ),
            {"now": now, "ticket_id": ticket_id},
        )
    await _apply_queue_snapshot(
        db,
        ticket_id,
        queue_snap,
        status="in_progress",
        sync_support_line=True,
    )

    await _change_ticket_support_line(
        db,
        ticket_id=ticket_id,
        from_line=from_line,
        to_line=queue_line_to_legacy_support_line(queue_snap["queue_line"]),
        changed_by=author_id,
        now=now,
    )

    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=author_id,
        now=now,
        event_type="escalated_to_engineers",
        payload={
            "queue_line": queue_snap["queue_line"],
            "action_by": queue_snap["action_by"],
            "chat_turn": queue_snap["chat_turn"],
            "action_since": _iso(queue_snap["action_since"]),
            "from_line": from_line,
            "to_line": queue_line_to_legacy_support_line(queue_snap["queue_line"]),
        },
    )

    if new_category_id is not None and old_category_id != new_category_id:
        _add_line_history_event(
            db,
            ticket_id=ticket_id,
            changed_by=author_id,
            now=now,
            event_type="category_changed",
            payload={
                "from_category_id": int(old_category_id) if old_category_id is not None else None,
                "to_category_id": new_category_id,
            },
        )

    text_clean = (comment or "").strip()
    src = str(row.get("source") or "call_center")
    if text_clean and is_lk_ticket_source(src):
        db.add(
            TrackerComments(
                ticket_id=ticket_id,
                author_id=author_id,
                body=text_clean,
            )
        )
    elif text_clean and is_internal_staff_chat_source(src):
        db.add(
            TrackerMessages(
                ticket_id=ticket_id,
                author_id=author_id,
                body=text_clean,
                created_at=now,
                person_type="skystream",
            )
        )
        await _apply_staff_chat_queue_update(
            db, ticket_id, operator_role="support", at=now,
        )

    await db.commit()
    return await load_ticket_detail(db, ticket_id, author_id)


async def close_ticket(
    db: AsyncSession,
    ticket_id: int,
    category_id: int,
    comment: str | None,
    author_id: int,
) -> dict[str, Any]:
    """Закрытие тикета с подтверждением категории и опциональным служебным комментарием."""
    row = await _load_ticket_row_for_line_ops(db, ticket_id)
    catalog = catalog_source_for_ticket(row.get("source"))
    await _validate_leaf_category(db, category_id=category_id, catalog_source=catalog)

    now = datetime.now(timezone.utc)
    old_category_id = row.get("category_id")
    new_category_id = int(category_id)
    old_status = str(row.get("status") or "")

    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET status = 'closed',
                category_id = :category_id,
                date_of_close = :now,
                closed_by = :closed_by,
                updated_at = :now
            WHERE id = :ticket_id
            """
        ),
        {
            "category_id": new_category_id,
            "now": now,
            "closed_by": author_id,
            "ticket_id": ticket_id,
        },
    )

    await _record_ticket_closed_history(
        db,
        ticket_id=ticket_id,
        changed_by=author_id,
        now=now,
        from_status=old_status,
    )

    if old_category_id != new_category_id:
        _add_line_history_event(
            db,
            ticket_id=ticket_id,
            changed_by=author_id,
            now=now,
            event_type="category_changed",
            payload={
                "from_category_id": int(old_category_id) if old_category_id is not None else None,
                "to_category_id": new_category_id,
            },
        )

    text_clean = (comment or "").strip()
    if text_clean:
        db.add(
            TrackerComments(
                ticket_id=ticket_id,
                author_id=author_id,
                body=text_clean,
            )
        )

    await db.commit()
    return await load_ticket_detail(db, ticket_id, author_id)


async def reopen_ticket(db: AsyncSession, ticket_id: int, author_id: int) -> dict[str, Any]:
    """Переоткрытие закрытого тикета в течение 24 ч после date_of_close."""
    row = (
        await db.execute(
            text(
                """
                SELECT id, status::text AS status, date_of_close, support_line
                FROM users.tracker_tickets
                WHERE id = :id
                """
            ),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Тикет не найден")

    old_status = str(row["status"] or "")
    closed_at = row.get("date_of_close")
    if not ticket_can_reopen(old_status, closed_at):
        if old_status not in TRACKER_CLOSED_STATUSES:
            raise HTTPException(status_code=400, detail="Тикет не закрыт")
        if not closed_at:
            raise HTTPException(status_code=400, detail="Переоткрытие недоступно для этого тикета")
        raise HTTPException(
            status_code=400,
            detail="Переоткрытие доступно только в течение 24 часов после закрытия",
        )

    now = datetime.now(timezone.utc)
    new_status = "in_progress"
    support_line = int(row["support_line"] or 1)
    queue_line = support_line_to_queue_line(support_line)

    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET status = :status,
                date_of_close = NULL,
                assigned_to = CASE WHEN :queue_line = 'cs' THEN :assigned_to ELSE assigned_to END,
                updated_at = :now
            WHERE id = :ticket_id
            """
        ),
        {
            "status": new_status,
            "assigned_to": author_id,
            "queue_line": queue_line,
            "now": now,
            "ticket_id": ticket_id,
        },
    )
    if queue_line == "cs":
        await _apply_queue_snapshot(
            db,
            ticket_id,
            on_register_call_cs(at=now),
            status=new_status,
        )
    elif queue_line == "engineers":
        await _apply_queue_snapshot(
            db,
            ticket_id,
            on_escalate_to_engineers(chat_turn="subscriber", at=now),
            status=new_status,
        )
    else:
        await _apply_queue_snapshot(
            db,
            ticket_id,
            {
                "queue_line": "partner",
                "action_by": "partner",
                "chat_turn": "subscriber",
                "action_since": now,
            },
            status=new_status,
        )

    await _record_ticket_reopened_history(
        db,
        ticket_id=ticket_id,
        changed_by=author_id,
        now=now,
        from_status=old_status,
        to_status=new_status,
        support_line=support_line,
    )
    if queue_line == "cs":
        await register_ticket_co_executor(db, ticket_id, author_id)

    await db.commit()
    return await load_ticket_detail(db, ticket_id, author_id)


async def take_ticket_back_to_ks(
    db: AsyncSession,
    ticket_id: int,
    author_id: int,
) -> dict[str, Any]:
    """Вернуть тикет на линию КС (support_line=1) и взять в работу."""
    row = await _load_ticket_row_for_line_ops(db, ticket_id)
    await reconcile_ticket_queue_from_thread(db, ticket_id, source=row.get("source"))
    row = await _load_ticket_row_for_line_ops(db, ticket_id)
    from_line = int(row["support_line"] or 1)
    if _coerce_queue_line(row) != "engineers":
        raise HTTPException(status_code=400, detail="Тикет не на линии инженеров")

    now = datetime.now(timezone.utc)
    queue_snap = on_return_to_cs(
        chat_turn=_coerce_chat_turn(row),
        action_by=str(row.get("action_by") or "cs"),
        at=now,
    )
    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET engineer_id = NULL,
                assigned_to = COALESCE(assigned_to, :author_id),
                updated_at = :now
            WHERE id = :ticket_id
            """
        ),
        {"now": now, "ticket_id": ticket_id, "author_id": author_id},
    )
    await _apply_queue_snapshot(
        db,
        ticket_id,
        queue_snap,
        status="in_progress",
        sync_support_line=True,
    )

    to_line = queue_line_to_legacy_support_line(queue_snap["queue_line"])
    await register_ticket_co_executor(db, ticket_id, author_id)
    await _change_ticket_support_line(
        db,
        ticket_id=ticket_id,
        from_line=from_line,
        to_line=to_line,
        changed_by=author_id,
        now=now,
    )

    _add_line_history_event(
        db,
        ticket_id=ticket_id,
        changed_by=author_id,
        now=now,
        event_type="returned_to_cs",
        payload={
            "queue_line": queue_snap["queue_line"],
            "action_by": queue_snap["action_by"],
            "chat_turn": queue_snap["chat_turn"],
            "action_since": _iso(queue_snap["action_since"]),
            "from_line": from_line,
            "to_line": to_line,
        },
    )

    await db.commit()
    return await load_ticket_detail(db, ticket_id, author_id)


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
    since_id: int = 0,
    subscriber_display_name: str = "Абонент",
) -> list[dict[str, Any]]:
    answer_expr = """
        CASE WHEN um.user_id IS NOT NULL AND um.person_type IS NOT NULL
             THEN CASE WHEN um.person_type = 'user' THEN 0 ELSE 1 END
             ELSE um.answer END
    """
    since_sql = " AND um.id > :since_id" if since_id > 0 else ""
    rows = (
        await db.execute(
            text(
                f"""
                SELECT um.id AS msg_id, um.id_user_from, um.date_tz, um.updated_at,
                    um.person_type, um.user_id,
                    ({answer_expr}) AS answer,
                    um.text AS text_raw,
                    CASE WHEN um.file_new IS NULL OR um.file_new IN ('0', '') THEN NULL
                         ELSE um.file_new END AS legacy_file,
                    um.relay_msg_id,
                    su.full_name AS staff_full_name,
                    su.role AS staff_role
                FROM users.user_mail um
                LEFT JOIN users.skystream_users su
                    ON um.user_id = su.id AND COALESCE(um.person_type, '') = 'skystream'
                WHERE um.ticket_id = :ticket_id{since_sql}
                ORDER BY COALESCE(um.date_tz, to_timestamp(um.date)), um.id
                """
            ),
            {"ticket_id": ticket_id, "since_id": since_id},
        )
    ).mappings().all()

    if not rows and subscriber_id is not None:
        start_id, end_id = await _mail_link_bounds(db, ticket_id)
        if start_id is not None and end_id is not None:
            rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT um.id AS msg_id, um.id_user_from, um.date_tz, um.updated_at,
                            um.person_type, um.user_id,
                            ({answer_expr}) AS answer,
                            um.text AS text_raw,
                            CASE WHEN um.file_new IS NULL OR um.file_new IN ('0', '') THEN NULL
                                 ELSE um.file_new END AS legacy_file,
                            um.relay_msg_id,
                            su.full_name AS staff_full_name,
                            su.role AS staff_role
                        FROM users.user_mail um
                        LEFT JOIN users.skystream_users su
                            ON um.user_id = su.id AND COALESCE(um.person_type, '') = 'skystream'
                        WHERE um.id BETWEEN :start_id AND :end_id
                          AND :subscriber_id IN (um.id_user_from, um.id_user_to)
                          {since_sql}
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
                    SELECT DISTINCT msg_id FROM users.user_mail_reads
                    WHERE msg_id = ANY(:ids) AND person_type = ANY(:staff_types)
                    """
                ),
                {"ids": msg_ids, "staff_types": list(STAFF_READ_PERSON_TYPES)},
            )
        ).scalars().all()
        read_ids = {int(x) for x in read_rows}

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["msg_id"])
        is_bot = int(r.get("id_user_from") or 0) == 0
        is_out = int(r["answer"] or 0) == 1
        dt = r.get("date_tz")
        legacy = r.get("legacy_file")
        side, author_name = _classify_mail_message(
            viewer_id=viewer_id,
            is_bot=is_bot,
            is_out=is_out,
            person_type=r.get("person_type"),
            author_id=int(r["user_id"]) if r.get("user_id") is not None else None,
            staff_full_name=r.get("staff_full_name"),
            staff_role=r.get("staff_role"),
            subscriber_name=subscriber_display_name,
        )
        edit_meta = _message_edit_meta(updated_at=r.get("updated_at"))
        messages.append(
            {
                "id": mid,
                "side": side,
                "text": (r.get("text_raw") or "").strip(),
                "author_name": author_name,
                "author_role": _staff_author_role(r.get("staff_role"), side),
                "created_at_iso": _iso(dt) if isinstance(dt, datetime) else None,
                "has_read": True if is_bot or side == "me" else mid in read_ids,
                "reply_to_id": _parse_reply_to_id(r.get("relay_msg_id")),
                **edit_meta,
                "legacy_file_url": _media_url(legacy) if legacy else None,
                "attachments": att_map.get(mid, []),
            }
        )

    if not messages and include_initial_body and include_initial_body.strip() and since_id <= 0:
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

    return messages


async def load_tracker_messages(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    viewer_role: str,
    *,
    since_id: int = 0,
    subscriber_display_name: str = "Абонент",
) -> list[dict[str, Any]]:
    since_sql = " AND tm.id > :since_id" if since_id > 0 else ""
    rows = (
        await db.execute(
            text(
                f"""
                SELECT tm.id, tm.body, tm.created_at, tm.updated_at, tm.author_id, tm.person_type,
                    tm.reply_to_id, tm.is_edited,
                    su.full_name AS staff_full_name,
                    su.role AS staff_role
                FROM users.tracker_messages tm
                LEFT JOIN users.skystream_users su ON su.id = tm.author_id
                WHERE tm.ticket_id = :ticket_id{since_sql}
                ORDER BY tm.created_at, tm.id
                """
            ),
            {"ticket_id": ticket_id, "since_id": since_id},
        )
    ).mappings().all()

    msg_ids = [int(r["id"]) for r in rows]
    att_map = await _attachments_map(db, msg_ids, tracker=True)

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
                    {"ids": msg_ids, "staff_types": list(STAFF_READ_PERSON_TYPES)},
                )
            ).scalars().all()
        }

    messages: list[dict[str, Any]] = []
    for r in rows:
        mid = int(r["id"])
        author_id = int(r["author_id"])
        side, author_name = _classify_tracker_message(
            viewer_id=viewer_id,
            author_id=author_id,
            person_type=r.get("person_type"),
            staff_full_name=r.get("staff_full_name"),
            staff_role=r.get("staff_role"),
            subscriber_name=subscriber_display_name,
        )
        is_own = side == "me"
        edit_meta = _message_edit_meta(
            updated_at=r.get("updated_at"),
            is_edited_flag=bool(r.get("is_edited")),
        )
        messages.append(
            {
                "id": mid,
                "side": side,
                "text": (r.get("body") or "").strip(),
                "author_name": author_name,
                "author_role": _staff_author_role(r.get("staff_role"), side),
                "created_at_iso": _iso(r.get("created_at")),
                "has_read": is_own or mid in staff_read_ids,
                "reply_to_id": _parse_reply_to_id(r.get("reply_to_id")),
                **edit_meta,
                "legacy_file_url": None,
                "attachments": att_map.get(mid, []),
            }
        )
    return messages


def ticket_poll_snapshot_from_detail(detail: dict[str, Any]) -> dict[str, Any]:
    """Лёгкий снимок статуса для поллинга /messages?since_id=…"""
    return {
        "status": detail["status"],
        "status_label": detail["status_label"],
        "is_open": detail["is_open"],
        "can_reopen": bool(detail.get("can_reopen")),
        "can_reply": bool(detail.get("can_reply")),
        "date_of_close_iso": detail.get("date_of_close_iso"),
        "updated_at_iso": detail.get("updated_at_iso"),
        "queue_line": detail.get("queue_line") or "cs",
        "queue_line_label": detail.get("queue_line_label") or "КС",
        "action_by": detail.get("action_by") or "cs",
        "action_by_label": detail.get("action_by_label") or "КС",
        "chat_turn": detail.get("chat_turn") or "subscriber",
        "chat_turn_label": detail.get("chat_turn_label") or "Ждём абонента",
        "action_since_iso": detail.get("action_since_iso"),
        "list_highlight": detail.get("list_highlight") or "none",
        "communication_state": detail.get("communication_state"),
        "communication_label": detail.get("communication_label"),
    }


async def list_ticket_messages(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    viewer_role: str,
    *,
    limit: int = 40,
    before_id: int | None = None,
    after_id: int | None = None,
    around_id: int | None = None,
    since_id: int = 0,
) -> tuple[
    list[dict[str, Any]],
    str,
    dict[int, str],
    dict[int, list[dict[str, str]]],
    bool,
    bool,
    dict[str, Any] | None,
]:
    from app.api.v1.routers.helpdesk import ticket_chat_pages as chat_pages

    detail = await load_ticket_detail(db, ticket_id, viewer_id)
    mode = detail["chat_mode"]
    sub_display = detail.get("subscriber_display_name") or await fetch_subscriber_display_name(
        db, detail.get("user_id")
    )

    if mode == "tracker":
        raw, has_older, has_newer = await chat_pages.load_tracker_messages_paged(
            db,
            ticket_id,
            viewer_id,
            viewer_role,
            subscriber_display_name=sub_display,
            limit=limit,
            before_id=before_id,
            after_id=after_id,
            around_id=around_id,
            since_id=since_id,
        )
        unread = [
            m["id"]
            for m in raw
            if m["side"] not in ("me", "bot")
            and not m.get("has_read")
            and m["id"] > 0
        ]
        if unread:
            await mark_tracker_messages_read(db, ticket_id, viewer_id, unread)
            unread_set = set(unread)
            for m in raw:
                if m["id"] in unread_set:
                    m["has_read"] = True
        receipts, read_by = await load_tracker_outbound_read_receipts(db, ticket_id)
    else:
        raw, has_older, has_newer = await chat_pages.load_mail_messages_paged(
            db,
            ticket_id,
            detail.get("user_id"),
            viewer_id,
            subscriber_display_name=sub_display,
            limit=limit,
            before_id=before_id,
            after_id=after_id,
            around_id=around_id,
            since_id=since_id,
            include_initial_body=detail.get("body"),
        )
        unread = [
            m["id"]
            for m in raw
            if m["side"] not in ("me", "bot")
            and not m.get("has_read")
            and m["id"] > 0
        ]
        if unread:
            await mark_mail_messages_read(db, ticket_id, viewer_id, unread)
            unread_set = set(unread)
            for m in raw:
                if m["id"] in unread_set:
                    m["has_read"] = True
        receipts, read_by = await load_mail_subscriber_read_receipts(db, ticket_id)

    _attach_read_receipts(raw, receipts, read_by)
    await attach_reply_previews(
        db,
        raw,
        chat_mode=mode,
        viewer_id=viewer_id,
        subscriber_display_name=sub_display,
    )
    ticket_snapshot = ticket_poll_snapshot_from_detail(detail) if since_id > 0 else None
    return raw, mode, receipts, read_by, has_older, has_newer, ticket_snapshot


async def get_ticket_read_receipts(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
) -> tuple[str, dict[int, str], dict[int, list[dict[str, str]]]]:
    """Поллинг галочек: прочтения исходящих сообщений без загрузки ленты."""
    detail = await load_ticket_detail(db, ticket_id, viewer_id)
    mode = detail["chat_mode"]
    if mode == "tracker":
        return mode, *await load_tracker_outbound_read_receipts(db, ticket_id)
    return mode, *await load_mail_subscriber_read_receipts(db, ticket_id)


async def mark_tracker_messages_read(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    message_ids: list[int],
) -> None:
    """Прочтение входящих сообщений: только tracker_messages_reads, без смены v2-очереди."""
    if not message_ids:
        return
    for mid in message_ids:
        if mid <= 0:
            continue
        exists = (
            await db.execute(
                text(
                    """
                    SELECT 1 FROM users.tracker_messages
                    WHERE id = :mid AND ticket_id = :tid LIMIT 1
                    """
                ),
                {"mid": mid, "tid": ticket_id},
            )
        ).scalar()
        if not exists:
            continue
        await db.execute(
            text(
                """
                INSERT INTO users.tracker_messages_reads (msg_id, user_id, person_type, read_time)
                VALUES (:msg_id, :user_id, 'skystream', NOW())
                ON CONFLICT (msg_id, user_id, person_type) DO NOTHING
                """
            ),
            {"msg_id": mid, "user_id": viewer_id},
        )
    await db.commit()


async def mark_mail_messages_read(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    message_ids: list[int],
) -> None:
    """Прочтение входящих сообщений: только user_mail_reads, без смены v2-очереди."""
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


async def maybe_set_first_response_at(
    db: AsyncSession,
    ticket_id: int,
    operator_role: str | None,
) -> None:
    """SLA ЛК: первый ответ support фиксируется в tracker_tickets.first_response_at."""
    if (operator_role or "").lower() != "support":
        return
    await db.execute(
        text(
            """
            UPDATE users.tracker_tickets
            SET first_response_at = NOW()
            WHERE id = :ticket_id
              AND source = 'lk'
              AND first_response_at IS NULL
            """
        ),
        {"ticket_id": ticket_id},
    )


async def edit_ticket_message(
    db: AsyncSession,
    ticket_id: int,
    message_id: int,
    operator_id: int,
    viewer_role: str,
    text_body: str,
) -> dict[str, Any]:
    await _assert_ticket_open_for_write(db, ticket_id)
    detail = await load_ticket_detail(db, ticket_id, operator_id)
    mode = detail["chat_mode"]
    sub_display = detail.get("subscriber_display_name") or "Абонент"
    text_body = text_body.strip()

    if mode == "mail":
        await _assert_own_mail_message(db, ticket_id, message_id, operator_id)
        await db.execute(
            text(
                """
                UPDATE users.user_mail
                SET text = :text, updated_at = NOW()
                WHERE id = :mid AND ticket_id = :tid
                """
            ),
            {"text": text_body, "mid": message_id, "tid": ticket_id},
        )
    else:
        await _assert_own_tracker_message(db, ticket_id, message_id, operator_id)
        now = datetime.now(timezone.utc)
        await db.execute(
            text(
                """
                UPDATE users.tracker_messages
                SET body = :text, is_edited = TRUE, updated_at = :now
                WHERE id = :mid AND ticket_id = :tid
                """
            ),
            {"text": text_body, "now": now, "mid": message_id, "tid": ticket_id},
        )
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = NOW() WHERE id = :tid"),
        {"tid": ticket_id},
    )
    await db.commit()

    if mode == "mail":
        row = (
            await db.execute(
                text(
                    """
                    SELECT date_tz, updated_at, relay_msg_id,
                        CASE WHEN file_new IS NULL OR file_new IN ('0', '') THEN NULL
                             ELSE file_new END AS legacy_file
                    FROM users.user_mail WHERE id = :mid AND ticket_id = :tid
                    """
                ),
                {"mid": message_id, "tid": ticket_id},
            )
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        msg: dict[str, Any] = {
            "id": message_id,
            "side": "me",
            "text": text_body,
            "author_name": "Вы",
            "author_role": _staff_author_role(viewer_role, "me"),
            "created_at_iso": _iso(row.get("date_tz")),
            "has_read": True,
            "recipient_read_at_iso": None,
            "read_by": [],
            "reply_to_id": _parse_reply_to_id(row.get("relay_msg_id")),
            **_message_edit_meta(updated_at=row.get("updated_at")),
            "legacy_file_url": _media_url(row.get("legacy_file")),
            "attachments": [],
        }
    else:
        row = (
            await db.execute(
                text(
                    """
                    SELECT created_at, updated_at, reply_to_id, is_edited
                    FROM users.tracker_messages WHERE id = :mid AND ticket_id = :tid
                    """
                ),
                {"mid": message_id, "tid": ticket_id},
            )
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        msg = {
            "id": message_id,
            "side": "me",
            "text": text_body,
            "author_name": "Вы",
            "author_role": _staff_author_role(viewer_role, "me"),
            "created_at_iso": _iso(row.get("created_at")),
            "has_read": True,
            "recipient_read_at_iso": None,
            "read_by": [],
            "reply_to_id": _parse_reply_to_id(row.get("reply_to_id")),
            **_message_edit_meta(
                updated_at=row.get("updated_at"),
                is_edited_flag=bool(row.get("is_edited")),
            ),
            "legacy_file_url": None,
            "attachments": [],
        }

    await attach_reply_previews(
        db,
        [msg],
        chat_mode=mode,
        viewer_id=operator_id,
        subscriber_display_name=sub_display,
    )
    return msg


async def delete_ticket_message(
    db: AsyncSession,
    ticket_id: int,
    message_id: int,
    operator_id: int,
) -> None:
    await _assert_ticket_open_for_write(db, ticket_id)
    detail = await load_ticket_detail(db, ticket_id, operator_id)
    mode = detail["chat_mode"]
    if mode == "mail":
        await _assert_own_mail_message(db, ticket_id, message_id, operator_id)
        await db.execute(
            text("DELETE FROM users.user_mail WHERE id = :mid AND ticket_id = :tid"),
            {"mid": message_id, "tid": ticket_id},
        )
    else:
        await _assert_own_tracker_message(db, ticket_id, message_id, operator_id)
        await db.execute(
            text("DELETE FROM users.tracker_messages WHERE id = :mid AND ticket_id = :tid"),
            {"mid": message_id, "tid": ticket_id},
        )
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = NOW() WHERE id = :tid"),
        {"tid": ticket_id},
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
    operator_role: str | None = None,
    reply_to_id: int | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text_body = text_body.strip()
    if not text_body and (not file or not file.filename) and not (attachments or []):
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    ticket = (
        await db.execute(
            text("SELECT id, user_id FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).mappings().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    await _assert_ticket_open_for_write(db, ticket_id)
    if int(ticket["user_id"] or 0) != chat_id:
        raise HTTPException(status_code=400, detail="Абонент не привязан к тикету")

    await _assert_reply_target(db, ticket_id, reply_to_id, chat_mode="mail")

    moscow_ts = _moscow_ts()
    # legacy: single file in message; store as attachment row (file_new not used)
    extra_attachments: list[dict[str, Any]] = []
    if file and file.filename:
        up = await save_attachment_temp(file, ticket_id=ticket_id, user_id=chat_id)
        extra_attachments = finalize_upload_tokens([up["token"]], ticket_id=ticket_id)

    ins = (
        await db.execute(
            text(
                """
                INSERT INTO users.user_mail (
                    text, id_user_from, id_user_to, read, answer, date, file_new,
                    user_id, person_type, user_chat, ticket_id, ip_address, date_tz,
                    relay_msg_id
                )
                VALUES (
                    :text, :from_id, :to_id, '0', 1, :ts, :file_new,
                    :op_id, 'skystream', :chat_id, :ticket_id,
                    CAST(:ip AS inet), NOW(),
                    :relay_msg_id
                )
                RETURNING id, date_tz
                """
            ),
            {
                "text": text_body,
                "from_id": operator_id,
                "to_id": chat_id,
                "ts": moscow_ts,
                "file_new": "",
                "op_id": operator_id,
                "chat_id": chat_id,
                "ticket_id": ticket_id,
                "ip": client_ip or "127.0.0.1",
                "relay_msg_id": str(reply_to_id) if reply_to_id else None,
            },
        )
    ).mappings().first()
    msg_id = int(ins["id"])
    created = ins.get("date_tz")

    now = datetime.now(timezone.utc)
    await _maybe_claim_cs_assignee(db, ticket_id, operator_id, operator_role)
    await _apply_staff_chat_queue_update(
        db, ticket_id, operator_role=operator_role, at=now,
    )
    await maybe_set_first_response_at(db, ticket_id, operator_role)
    await db.commit()

    all_att = list(attachments or []) + list(extra_attachments or [])
    if all_att:
        for a in all_att:
            await db.execute(
                text(
                    """
                    INSERT INTO users.user_mail_attachments (msg_id, file_path, original_filename, file_ext, file_size_bytes)
                    VALUES (:msg_id, :file_path, :original_filename, :file_ext, :file_size_bytes)
                    """
                ),
                {
                    "msg_id": msg_id,
                    "file_path": a["file_path"],
                    "original_filename": a.get("original_filename") or "",
                    "file_ext": a.get("file_ext"),
                    "file_size_bytes": a.get("file_size_bytes"),
                },
            )
        await db.commit()

    att_items: list[dict[str, Any]] = []
    if all_att:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT id, file_path, original_filename, file_ext, file_size_bytes
                    FROM users.user_mail_attachments
                    WHERE msg_id = :mid
                    ORDER BY id ASC
                    """
                ),
                {"mid": msg_id},
            )
        ).mappings().all()
        for r in rows:
            fp = str(r.get("file_path") or "")
            ext = (r.get("file_ext") or "").lower()
            att_items.append(
                {
                    "id": int(r["id"]),
                    "file_path": fp,
                    "original_filename": r.get("original_filename") or "",
                    "file_ext": ext or None,
                    "file_size_bytes": int(r["file_size_bytes"]) if r.get("file_size_bytes") is not None else None,
                    "is_image": fp.lower().endswith(tuple(_IMAGE_EXT)) or ext.lstrip(".") in {e.lstrip(".") for e in _IMAGE_EXT},
                }
            )

    out: dict[str, Any] = {
        "id": msg_id,
        "side": "me",
        "text": text_body,
        "author_name": "Вы",
        "author_role": _staff_author_role(operator_role, "me"),
        "created_at_iso": _iso(created if isinstance(created, datetime) else now),
        "has_read": True,
        "recipient_read_at_iso": None,
        "read_by": [],
        "reply_to_id": reply_to_id,
        "is_edited": False,
        "legacy_file_url": None,
        "attachments": att_items,
    }
    if reply_to_id:
        enrich_reply_previews([out])
        if not out.get("reply_preview"):
            previews = await fetch_reply_previews_missing(
                db,
                [reply_to_id],
                chat_mode="mail",
                viewer_id=operator_id,
                subscriber_display_name="Абонент",
            )
            prev = previews.get(reply_to_id)
            out["reply_preview"] = prev if prev else _deleted_reply_preview(reply_to_id)
    return out


async def send_tracker_reply(
    db: AsyncSession,
    ticket_id: int,
    operator_id: int,
    text_body: str,
    *,
    operator_role: str | None = None,
    reply_to_id: int | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text_body = text_body.strip()
    if not text_body and not (attachments or []):
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    await _assert_ticket_open_for_write(db, ticket_id)
    await _assert_reply_target(db, ticket_id, reply_to_id, chat_mode="tracker")

    now = datetime.now(timezone.utc)
    msg = TrackerMessages(
        ticket_id=ticket_id,
        author_id=operator_id,
        body=text_body,
        created_at=now,
        person_type="skystream",
        reply_to_id=reply_to_id,
    )
    db.add(msg)
    await db.flush()
    await _maybe_claim_cs_assignee(db, ticket_id, operator_id, operator_role)
    await _apply_staff_chat_queue_update(
        db, ticket_id, operator_role=operator_role, at=now,
    )
    await maybe_set_first_response_at(db, ticket_id, operator_role)
    await db.commit()

    if attachments:
        objs = [
            TrackerMessageAttachment(
                msg_id=int(msg.id),
                file_path=a["file_path"],
                original_filename=a.get("original_filename") or "",
                file_ext=a.get("file_ext"),
                file_size_bytes=a.get("file_size_bytes"),
            )
            for a in attachments
        ]
        db.add_all(objs)
        await db.commit()

    att_items: list[dict[str, Any]] = []
    if attachments:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT id, file_path, original_filename, file_ext, file_size_bytes
                    FROM users.tracker_message_attachments
                    WHERE msg_id = :mid
                    ORDER BY id ASC
                    """
                ),
                {"mid": int(msg.id)},
            )
        ).mappings().all()
        for r in rows:
            fp = str(r.get("file_path") or "")
            ext = (r.get("file_ext") or "").lower()
            att_items.append(
                {
                    "id": int(r["id"]),
                    "file_path": fp,
                    "original_filename": r.get("original_filename") or "",
                    "file_ext": ext or None,
                    "file_size_bytes": int(r["file_size_bytes"]) if r.get("file_size_bytes") is not None else None,
                    "is_image": fp.lower().endswith(tuple(_IMAGE_EXT)) or ext.lstrip(".") in {e.lstrip(".") for e in _IMAGE_EXT},
                }
            )

    out: dict[str, Any] = {
        "id": int(msg.id),
        "side": "me",
        "text": text_body,
        "author_name": "Вы",
        "author_role": _staff_author_role(operator_role, "me"),
        "created_at_iso": _iso(now),
        "has_read": True,
        "recipient_read_at_iso": None,
        "read_by": [],
        "reply_to_id": reply_to_id,
        "is_edited": False,
        "attachments": att_items,
    }
    if reply_to_id:
        enrich_reply_previews([out])
        if not out.get("reply_preview"):
            previews = await fetch_reply_previews_missing(
                db,
                [reply_to_id],
                chat_mode="tracker",
                viewer_id=operator_id,
                subscriber_display_name="Абонент",
            )
            prev = previews.get(reply_to_id)
            out["reply_preview"] = prev if prev else _deleted_reply_preview(reply_to_id)
    return out


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


def _safe_name(name: str) -> str:
    raw = (name or "").strip().replace("\\", "/")
    base = raw.split("/")[-1] if raw else "file"
    keep = []
    for ch in base:
        if ch.isalnum() or ch in ("-", "_", ".", " "):
            keep.append(ch)
        else:
            keep.append("_")
    out = "".join(keep).strip(" .")
    return out or "file"


def _ext_from_name(filename: str) -> str:
    return os.path.splitext((filename or "").strip())[1].lower()


def _looks_like_allowed(content: bytes, ext: str) -> bool:
    if ext in (".jpg", ".jpeg"):
        return content.startswith(b"\xFF\xD8\xFF")
    if ext == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".gif":
        return content.startswith(b"GIF87a") or content.startswith(b"GIF89a")
    if ext == ".webp":
        return len(content) > 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    if ext == ".bmp":
        return content.startswith(b"BM")
    if ext == ".pdf":
        return content.startswith(b"%PDF-")
    if ext in (".xlsx", ".docx"):
        return content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06") or content.startswith(b"PK\x07\x08")
    if ext in (".xls", ".doc"):
        return content.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")
    if ext == ".csv":
        if b"\x00" in content:
            return False
        return True
    return False


def _media_abs(rel_path: str) -> str:
    p = os.path.abspath(os.path.join(_MEDIA_ROOT, rel_path.lstrip("/")))
    root = os.path.abspath(_MEDIA_ROOT)
    if not (p == root or p.startswith(root + os.sep)):
        raise HTTPException(status_code=400, detail="Некорректный путь файла")
    return p


def _rel_from_media_url(url: str) -> str | None:
    if not url:
        return None
    u = url.strip()
    if u.startswith("/media/"):
        return u[len("/media/") :]
    if u.startswith("media/"):
        return u[len("media/") :]
    return None


def _make_chat_folder(user_id: int | None) -> str:
    return str(int(user_id)) if user_id and int(user_id) > 0 else "no_user"


async def save_attachment_temp(
    file: UploadFile,
    *,
    ticket_id: int,
    user_id: int | None,
) -> dict[str, Any]:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Файл не передан")
    ext = _ext_from_name(file.filename)
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Разрешены изображения, PDF, Excel, CSV")
    contents = await file.read()
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Файл больше 15 МБ")
    if not _looks_like_allowed(contents, ext):
        raise HTTPException(status_code=400, detail="Файл не похож на заявленный формат")

    folder = _make_chat_folder(user_id)
    tmp_name = f"{uuid.uuid4().hex}{ext}"
    rel_dir = os.path.join("chat", folder, str(int(ticket_id)), "tmp")
    os.makedirs(_media_abs(rel_dir), exist_ok=True)
    rel_path = os.path.join(rel_dir, tmp_name)
    abs_path = _media_abs(rel_path)
    with open(abs_path, "wb") as f:
        f.write(contents)

    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "typ": "ticket_upload",
        "ticket_id": int(ticket_id),
        "tmp_rel": rel_path.replace("\\", "/"),
        "orig": _safe_name(file.filename),
        "ext": ext,
        "size": int(len(contents)),
        "folder": folder,
        "iat": now,
        "exp": now + _UPLOAD_TOKEN_TTL_SEC,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {
        "token": token,
        "original_filename": payload["orig"],
        "file_ext": ext,
        "file_size_bytes": payload["size"],
        "is_image": ext in _IMAGE_EXT,
    }


def _decode_upload_token(token: str, *, ticket_id: int) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный токен загрузки")
    if payload.get("typ") != "ticket_upload":
        raise HTTPException(status_code=400, detail="Некорректный токен загрузки")
    if int(payload.get("ticket_id") or 0) != int(ticket_id):
        raise HTTPException(status_code=400, detail="Токен не для этого тикета")
    return payload


def _final_rel_path(*, folder: str, ticket_id: int, original_filename: str, ext: str) -> str:
    base = os.path.splitext(_safe_name(original_filename))[0]
    stamp = int(datetime.now(_MOSCOW).timestamp())
    uniq = uuid.uuid4().hex[:10]
    fname = f"{base}_{stamp}_{uniq}{ext}"
    rel_dir = os.path.join("chat", folder, str(int(ticket_id)))
    return os.path.join(rel_dir, fname).replace("\\", "/")


def finalize_upload_tokens(
    tokens: list[str],
    *,
    ticket_id: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tokens:
        payload = _decode_upload_token(t, ticket_id=ticket_id)
        tmp_rel = str(payload["tmp_rel"])
        abs_tmp = _media_abs(tmp_rel)
        if not os.path.exists(abs_tmp):
            raise HTTPException(status_code=400, detail="Загруженный файл не найден")
        folder = str(payload.get("folder") or "no_user")
        ext = str(payload.get("ext") or "")
        orig = str(payload.get("orig") or "file")
        size = int(payload.get("size") or 0)
        rel_final = _final_rel_path(folder=folder, ticket_id=ticket_id, original_filename=orig, ext=ext)
        abs_final = _media_abs(rel_final)
        os.makedirs(os.path.dirname(abs_final), exist_ok=True)
        os.replace(abs_tmp, abs_final)
        url = _media_url(rel_final)
        if not url:
            raise HTTPException(status_code=500, detail="Ошибка сохранения файла")
        out.append(
            {
                "file_path": url,
                "original_filename": orig,
                "file_ext": ext.lstrip(".") if ext else None,
                "file_size_bytes": size or None,
                "is_image": ext in _IMAGE_EXT,
            }
        )
    return out


async def detach_ticket_attachment(
    db: AsyncSession,
    *,
    ticket_id: int,
    message_id: int,
    attachment_id: int,
    operator_id: int,
) -> None:
    detail = await load_ticket_detail(db, ticket_id, operator_id)
    mode = detail["chat_mode"]
    if mode == "mail":
        await _assert_own_mail_message(db, ticket_id, message_id, operator_id)
        row = (
            await db.execute(
                text(
                    """
                    SELECT file_path FROM users.user_mail_attachments
                    WHERE id = :aid AND msg_id = :mid
                    LIMIT 1
                    """
                ),
                {"aid": attachment_id, "mid": message_id},
            )
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Вложение не найдено")
        await db.execute(
            text(
                "DELETE FROM users.user_mail_attachments WHERE id = :aid AND msg_id = :mid"
            ),
            {"aid": attachment_id, "mid": message_id},
        )
        await db.commit()
        rel = _rel_from_media_url(str(row.get("file_path") or ""))
        if rel:
            abs_path = _media_abs(rel)
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except OSError:
                pass
        return

    await _assert_own_tracker_message(db, ticket_id, message_id, operator_id)
    row = (
        await db.execute(
            text(
                """
                SELECT file_path FROM users.tracker_message_attachments
                WHERE id = :aid AND msg_id = :mid
                LIMIT 1
                """
            ),
            {"aid": attachment_id, "mid": message_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Вложение не найдено")
    await db.execute(
        text(
            "DELETE FROM users.tracker_message_attachments WHERE id = :aid AND msg_id = :mid"
        ),
        {"aid": attachment_id, "mid": message_id},
    )
    await db.commit()
    rel = _rel_from_media_url(str(row.get("file_path") or ""))
    if rel:
        abs_path = _media_abs(rel)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except OSError:
            pass


def _comment_staff_label(role: str | None) -> str:
    if (role or "").strip().lower() == "engineer":
        return "Инженер"
    return "Контактный сервис"


def _comment_side(*, author_id: int, viewer_id: int, role: str | None) -> tuple[str, str]:
    if author_id == viewer_id:
        return ("me", "Вы")
    label = _comment_staff_label(role)
    if (role or "").strip().lower() == "engineer":
        return ("engineer", label)
    return ("support", label)


def _comment_row_to_item(row: Any, viewer_id: int) -> dict[str, Any]:
    author_id = int(row["author_id"])
    role = row.get("author_role")
    side, author_name = _comment_side(author_id=author_id, viewer_id=viewer_id, role=role)
    updated = row.get("updated_ad")
    edit_meta = _message_edit_meta(updated_at=updated if isinstance(updated, datetime) else None)
    return {
        "id": int(row["id"]),
        "side": side,
        "text": (row.get("text") or "").strip(),
        "author_name": author_name,
        "is_me": author_id == viewer_id,
        "created_at_iso": _iso(row.get("created_at")),
        **edit_meta,
    }


async def _assert_ticket_exists_for_comments(db: AsyncSession, ticket_id: int) -> None:
    exists = (
        await db.execute(
            text("SELECT 1 FROM users.tracker_tickets WHERE id = :id"),
            {"id": ticket_id},
        )
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Тикет не найден")


def _validate_comment_text(text: str) -> None:
    clean = (text or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Введите текст комментария")
    if len(clean) > 8000:
        raise HTTPException(status_code=400, detail="Комментарий слишком длинный")


_COMMENT_SELECT = """
    SELECT c.id, c.author_id, c.text, c.created_at, c.updated_ad,
           su.role AS author_role
    FROM users.tracker_comments c
    LEFT JOIN users.skystream_users su ON su.id = c.author_id
    WHERE c.ticket_id = :ticket_id
"""


async def list_ticket_comments(
    db: AsyncSession,
    ticket_id: int,
    viewer_id: int,
    *,
    limit: int = 40,
    before_id: int | None = None,
    after_id: int | None = None,
    since_id: int = 0,
) -> tuple[list[dict[str, Any]], bool, bool]:
    await _assert_ticket_exists_for_comments(db, ticket_id)
    lim = max(1, min(int(limit), 100))

    if since_id > 0 and before_id is None and after_id is None:
        rows = (
            await db.execute(
                text(
                    f"""
                    {_COMMENT_SELECT}
                      AND c.id > :since_id
                    ORDER BY c.id ASC
                    """
                ),
                {"ticket_id": ticket_id, "since_id": since_id},
            )
        ).mappings().all()
        items = [_comment_row_to_item(r, viewer_id) for r in rows]
        return items, False, False

    if before_id is not None and before_id > 0:
        rows = (
            await db.execute(
                text(
                    f"""
                    {_COMMENT_SELECT}
                      AND c.id < :before_id
                    ORDER BY c.id DESC
                    LIMIT :lim
                    """
                ),
                {"ticket_id": ticket_id, "before_id": before_id, "lim": lim},
            )
        ).mappings().all()
        rows = list(reversed(rows))
        has_older = bool(
            (
                await db.execute(
                    text(
                        f"""
                        SELECT 1 FROM users.tracker_comments c
                        WHERE c.ticket_id = :ticket_id AND c.id < :first_id
                        LIMIT 1
                        """
                    ),
                    {"ticket_id": ticket_id, "first_id": int(rows[0]["id"]) if rows else before_id},
                )
            ).scalar()
        )
        items = [_comment_row_to_item(r, viewer_id) for r in rows]
        return items, has_older, False

    if after_id is not None and after_id > 0:
        rows = (
            await db.execute(
                text(
                    f"""
                    {_COMMENT_SELECT}
                      AND c.id > :after_id
                    ORDER BY c.id ASC
                    LIMIT :lim
                    """
                ),
                {"ticket_id": ticket_id, "after_id": after_id, "lim": lim},
            )
        ).mappings().all()
        has_newer = bool(
            (
                await db.execute(
                    text(
                        f"""
                        SELECT 1 FROM users.tracker_comments c
                        WHERE c.ticket_id = :ticket_id AND c.id > :last_id
                        LIMIT 1
                        """
                    ),
                    {
                        "ticket_id": ticket_id,
                        "last_id": int(rows[-1]["id"]) if rows else after_id,
                    },
                )
            ).scalar()
        )
        items = [_comment_row_to_item(r, viewer_id) for r in rows]
        return items, False, has_newer

    rows = (
        await db.execute(
            text(
                f"""
                {_COMMENT_SELECT}
                ORDER BY c.id DESC
                LIMIT :lim
                """
            ),
            {"ticket_id": ticket_id, "lim": lim},
        )
    ).mappings().all()
    rows = list(reversed(rows))
    has_older = False
    if rows:
        has_older = bool(
            (
                await db.execute(
                    text(
                        """
                        SELECT 1 FROM users.tracker_comments c
                        WHERE c.ticket_id = :ticket_id AND c.id < :first_id
                        LIMIT 1
                        """
                    ),
                    {"ticket_id": ticket_id, "first_id": int(rows[0]["id"])},
                )
            ).scalar()
        )
    items = [_comment_row_to_item(r, viewer_id) for r in rows]
    return items, has_older, False


async def send_ticket_comment(
    db: AsyncSession,
    ticket_id: int,
    author_id: int,
    text_body: str,
) -> dict[str, Any]:
    await _assert_ticket_open_for_write(db, ticket_id)
    await _assert_ticket_exists_for_comments(db, ticket_id)
    _validate_comment_text(text_body)
    clean = text_body.strip()
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            text(
                """
                INSERT INTO users.tracker_comments (ticket_id, author_id, text)
                VALUES (:ticket_id, :author_id, :text)
                RETURNING id
                """
            ),
            {"ticket_id": ticket_id, "author_id": author_id, "text": clean},
        )
    ).mappings().first()
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = :now WHERE id = :tid"),
        {"now": now, "tid": ticket_id},
    )
    await db.commit()
    cid = int(row["id"])
    loaded = (
        await db.execute(
            text(f"{_COMMENT_SELECT} AND c.id = :cid"),
            {"ticket_id": ticket_id, "cid": cid},
        )
    ).mappings().first()
    if not loaded:
        raise HTTPException(status_code=500, detail="Не удалось создать комментарий")
    return _comment_row_to_item(loaded, author_id)


async def edit_ticket_comment(
    db: AsyncSession,
    ticket_id: int,
    comment_id: int,
    author_id: int,
    text_body: str,
) -> dict[str, Any]:
    await _assert_ticket_open_for_write(db, ticket_id)
    await _assert_ticket_exists_for_comments(db, ticket_id)
    _validate_comment_text(text_body)
    clean = text_body.strip()
    now = datetime.now(timezone.utc)
    updated = (
        await db.execute(
            text(
                """
                UPDATE users.tracker_comments
                SET text = :text, updated_ad = :now
                WHERE id = :cid AND ticket_id = :tid AND author_id = :aid
                RETURNING id
                """
            ),
            {"text": clean, "now": now, "cid": comment_id, "tid": ticket_id, "aid": author_id},
        )
    ).mappings().first()
    if not updated:
        raise HTTPException(status_code=404, detail="Комментарий не найден или нет прав на изменение")
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = :now WHERE id = :tid"),
        {"now": now, "tid": ticket_id},
    )
    await db.commit()
    loaded = (
        await db.execute(
            text(f"{_COMMENT_SELECT} AND c.id = :cid"),
            {"ticket_id": ticket_id, "cid": comment_id},
        )
    ).mappings().first()
    return _comment_row_to_item(loaded, author_id)


async def delete_ticket_comment(
    db: AsyncSession,
    ticket_id: int,
    comment_id: int,
    author_id: int,
) -> None:
    await _assert_ticket_open_for_write(db, ticket_id)
    await _assert_ticket_exists_for_comments(db, ticket_id)
    res = await db.execute(
        text(
            """
            DELETE FROM users.tracker_comments
            WHERE id = :cid AND ticket_id = :tid AND author_id = :aid
            """
        ),
        {"cid": comment_id, "tid": ticket_id, "aid": author_id},
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Комментарий не найден или нет прав на удаление")
    now = datetime.now(timezone.utc)
    await db.execute(
        text("UPDATE users.tracker_tickets SET updated_at = :now WHERE id = :tid"),
        {"now": now, "tid": ticket_id},
    )
    await db.commit()
