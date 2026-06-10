"""Модель очереди тикетов v2 и правила подсветки (без привязки к legacy status).

Колонки на tracker_tickets:
  queue_line   — линия ТП: cs | engineers | partner
  action_by    — у кого «мяч»: cs | engineers | partner | subscriber | external
  chat_turn    — чат с абонентом: staff | subscriber
  action_since — с какого момента (сортировка)

Линии:
  cs, engineers — staff helpdesk (этот сайт)
  partner       — 3-я линия (партнёр/техник; person_type partner|tech в tracker_messages)
  external      — не линия ТП, а пауза: запчасти, логистика (status waiting_parts и т.п.)

Правила (handlers):
  • source=lk — чат с абонентом:
      абонент написал → chat_turn=staff, action_by=queue_line
      staff ответил → chat_turn=subscriber, action_by=subscriber
  • source=call_center|abs — внутренний чат КС ↔ инженеры (без subscriber):
      КС написал → chat_turn=staff, action_by=engineers
      инженер написал → chat_turn=staff, action_by=cs
      покой (регистрация звонка) → chat_turn=subscriber, action_by=cs
  • Эскалация на инженеров / партнёра:
      queue_line=engineers|partner, action_by=engineers|partner
  • Возврат на КС:
      queue_line=cs, action_by=cs
  • Ждём запчасти/логистику:
      action_by=external (queue_line обычно не меняется)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypedDict

TrackerQueueLine = Literal["cs", "engineers", "partner"]
TrackerActionBy = Literal["cs", "engineers", "partner", "subscriber", "external"]
TrackerChatTurn = Literal["staff", "subscriber"]
StaffParty = Literal["cs", "engineers"]
ViewerRole = Literal["support", "engineer", "partner", "technician", "director", "admin"]

QueueLine = TrackerQueueLine
ActionBy = TrackerActionBy
ChatTurn = TrackerChatTurn

_LINE_TO_ACTION: dict[TrackerQueueLine, TrackerActionBy] = {
    "cs": "cs",
    "engineers": "engineers",
    "partner": "partner",
}


class TicketQueueSnapshot(TypedDict):
    queue_line: TrackerQueueLine
    action_by: TrackerActionBy
    chat_turn: TrackerChatTurn
    action_since: datetime | None


def support_line_to_queue_line(support_line: int) -> TrackerQueueLine:
    if support_line == 2:
        return "engineers"
    if support_line == 3:
        return "partner"
    return "cs"


def queue_line_to_legacy_support_line(queue_line: TrackerQueueLine) -> int:
    if queue_line == "engineers":
        return 2
    if queue_line == "partner":
        return 3
    return 1


def on_subscriber_public_message(
    queue_line: TrackerQueueLine,
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Абонент написал в публичный чат."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": queue_line,
        "action_by": _LINE_TO_ACTION[queue_line],
        "chat_turn": "staff",
        "action_since": now,
    }


def on_staff_public_reply(
    queue_line: TrackerQueueLine,
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """КС / инженер / партнёр ответил абоненту (source=lk)."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": queue_line,
        "action_by": "subscriber",
        "chat_turn": "subscriber",
        "action_since": now,
    }


def on_internal_staff_message(
    author: StaffParty,
    queue_line: TrackerQueueLine,
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Сообщение staff в чате call_center/abs: ход передаётся другой линии (без абонента)."""
    now = at or datetime.now(timezone.utc)
    counterparty: TrackerActionBy = "engineers" if author == "cs" else "cs"
    return {
        "queue_line": queue_line,
        "action_by": counterparty,
        "chat_turn": "staff",
        "action_since": now,
    }


def _preserve_chat_action_by(
    chat_turn: TrackerChatTurn,
    action_by: str,
    *,
    idle_action_by: TrackerActionBy,
) -> TrackerActionBy:
    """При смене линии не сбрасывать «мяч» в internal/lk-чате."""
    if chat_turn == "subscriber":
        return idle_action_by
    ab = (action_by or "").strip()
    if ab in ("cs", "engineers", "partner"):
        return ab  # type: ignore[return-value]
    return idle_action_by


def on_escalate_to_engineers(
    *,
    chat_turn: TrackerChatTurn = "staff",
    action_by: str | None = None,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    now = at or datetime.now(timezone.utc)
    ab = _preserve_chat_action_by(
        chat_turn,
        action_by or "engineers",
        idle_action_by="engineers",
    )
    return {
        "queue_line": "engineers",
        "action_by": ab,
        "chat_turn": chat_turn,
        "action_since": now,
    }


def on_escalate_to_partner(
    *,
    chat_turn: TrackerChatTurn = "staff",
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Передача на 3-ю линию (партнёр/техник)."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": "partner",
        "action_by": "partner",
        "chat_turn": chat_turn,
        "action_since": now,
    }


def on_return_to_cs(
    *,
    chat_turn: TrackerChatTurn = "subscriber",
    action_by: str | None = None,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Инженеры или партнёр вернули тикет на КС."""
    now = at or datetime.now(timezone.utc)
    ab = _preserve_chat_action_by(
        chat_turn,
        action_by or "cs",
        idle_action_by="cs",
    )
    return {
        "queue_line": "cs",
        "action_by": ab,
        "chat_turn": chat_turn,
        "action_since": now,
    }


def on_external_wait(
    queue_line: TrackerQueueLine,
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Ждём запчасти, логистику (не путать с линией partner)."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": queue_line,
        "action_by": "external",
        "chat_turn": "subscriber",
        "action_since": now,
    }


def on_register_call_cs(
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Регистрация звонка оператором КС: тикет в работе, чат не ждёт ответа."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": "cs",
        "action_by": "cs",
        "chat_turn": "subscriber",
        "action_since": now,
    }


def on_register_new_subscriber_lead(
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Лид «новый абонент»: КС доводит до регистрации."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": "cs",
        "action_by": "cs",
        "chat_turn": "staff",
        "action_since": now,
    }


def on_register_partner_prospect(
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Лид «новый партнёр»: очередь менеджера (support_line=4), не требует ответа КС."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": "cs",
        "action_by": "cs",
        "chat_turn": "subscriber",
        "action_since": now,
    }


def on_partner_technician_wait(
    *,
    at: datetime | None = None,
) -> TicketQueueSnapshot:
    """Ждём выезд/действие техника партнёра (waiting_technician, no_technician)."""
    now = at or datetime.now(timezone.utc)
    return {
        "queue_line": "partner",
        "action_by": "partner",
        "chat_turn": "subscriber",
        "action_since": now,
    }


def _viewer_line_role(viewer_role: ViewerRole) -> Literal["support", "engineer", "partner"] | None:
    if viewer_role == "support":
        return "support"
    if viewer_role == "engineer":
        return "engineer"
    if viewer_role in ("partner", "technician"):
        return "partner"
    return None


def communication_state_from_v2(
    chat_turn: str,
    action_by: str,
    *,
    source: str | None = None,
) -> Literal["needs_reply", "awaiting_subscriber"] | None:
    """Подпись колонки «Статус» для открытых тикетов (не workflow)."""
    from app.constants import is_internal_staff_chat_source, is_subscriber_chat_source

    src = (source or "").strip()
    if chat_turn == "staff" and action_by in ("cs", "engineers", "partner"):
        if is_internal_staff_chat_source(src):
            return None
        return "needs_reply"
    if chat_turn == "subscriber" and is_subscriber_chat_source(src):
        return "awaiting_subscriber"
    if chat_turn == "subscriber" and is_internal_staff_chat_source(src):
        return None
    if chat_turn == "subscriber":
        return "awaiting_subscriber"
    return None


def list_highlight_for_viewer(
    state: TicketQueueSnapshot,
    *,
    viewer_role: ViewerRole,
    has_unread: bool = False,
    workflow_status: str | None = None,
    source: str | None = None,
    support_line: int = 1,
) -> Literal["chat", "ops", "none"]:
    """Подсветка строки в списке для КС, инженера или партнёра."""
    from app.constants import is_manager_support_line, is_subscriber_chat_source

    line_role = _viewer_line_role(viewer_role)
    if line_role is None:
        return "none"

    if line_role == "support" and is_manager_support_line(support_line):
        return "none"

    action = state["action_by"]
    chat_pending = state["chat_turn"] == "staff"
    st = (workflow_status or "").strip()
    src = (source or "").strip()

    # ЛК: КС — первая линия, видят «нужен ответ staff» даже на линии инженеров
    if (
        is_subscriber_chat_source(src)
        and line_role == "support"
        and chat_pending
        and action in ("cs", "engineers", "partner")
    ):
        return "chat"

    if chat_pending and action == "cs" and line_role == "support":
        return "chat"
    if chat_pending and action == "engineers" and line_role == "engineer":
        return "chat"
    if chat_pending and action == "partner" and line_role == "partner":
        return "chat"

    if (
        line_role == "support"
        and action == "cs"
        and st in ("waiting_cs", "cc_handover")
    ):
        return "ops"

    if has_unread:
        if line_role == "support" and state["queue_line"] == "cs":
            return "chat"
        if line_role == "engineer" and state["queue_line"] == "engineers":
            return "chat"
        if line_role == "partner" and state["queue_line"] == "partner":
            return "chat"

    return "none"
