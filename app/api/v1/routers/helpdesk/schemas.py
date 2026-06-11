from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.api.v1.routers.helpdesk.user_profile_schemas import TicketSubscriberAccountSummary


class TicketStaffParticipant(BaseModel):
    id: int
    label: str
    role: str = "support"
    is_primary: bool = False
    """Основной исполнитель (assigned_to)."""
    is_viewer: bool = False


class TrackerTicketListItem(BaseModel):
    id: int
    title: str
    object_type: str
    status: str
    status_label: str
    priority: Optional[str] = None
    priority_label: Optional[str] = None
    support_line: int
    support_line_label: str
    queue_line: str = "cs"
    action_by: str = "cs"
    chat_turn: str = "staff"
    action_since: Optional[datetime] = None
    list_highlight: str = "none"
    """chat — нужен ответ в переписке; ops — операционное действие КС; none."""
    source: Optional[str] = None
    source_label: str
    category_label: Optional[str] = None
    user_id: Optional[int] = None
    subscriber_profile_user_id: Optional[int] = None
    """Для object_type=user — ссылка на карточку /users/{id}."""
    subscriber_is_juridical: int = 0
    """0 — физлицо; 2 — юрлицо (золотой заголовок тикета в UI)."""
    subscriber_name: Optional[str] = None
    subscriber_login: Optional[str] = None
    assignee_label: Optional[str] = None
    """Текст колонки «Исполнитель» (только assigned_to; без ФИО для engineer/manager)."""
    assignee_role: Optional[str] = None
    assignee_is_viewer: bool = False
    """True, если assigned_to — текущий оператор."""
    assigned_to: Optional[int] = None
    has_unread: bool = False
    """Есть сообщения абонента, которые ещё не прочитал ни один сотрудник."""
    communication_state: Optional[str] = None
    """needs_reply | awaiting_subscriber"""
    communication_label: Optional[str] = None
    date_of_create: datetime
    updated_at: Optional[datetime] = None
    date_of_close: Optional[datetime] = None
    rating: Optional[int] = None
    rating_comment: Optional[str] = None


class UnreadTicketsResponse(BaseModel):
    unread_count: int = 0


class OperatorTicketMonthStatsResponse(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    date_from: str
    date_to: str
    open_count: int = 0
    closed_count: int = 0


class OperatorManageItem(BaseModel):
    id: int
    login: str
    full_name: str | None = None
    email: str | None = None
    is_active: bool = True
    is_online: bool = False
    level: int | None = None
    open_tickets_count: int = 0
    last_activity: str | None = None


class OperatorManageStats(BaseModel):
    active_count: int = 0
    online_count: int = 0


class OperatorManagePagination(BaseModel):
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=1)


class OperatorManageListResponse(BaseModel):
    admins: list[OperatorManageItem] = []
    operators: list[OperatorManageItem] = []
    stats: OperatorManageStats
    operators_pagination: OperatorManagePagination


class OperatorSuggestedLoginResponse(BaseModel):
    login: str


class OperatorCreateRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=10, max_length=10)
    full_name: str = Field(..., min_length=1, max_length=256)
    email: str | None = Field(None, max_length=256)


class OperatorUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=256)
    is_active: bool | None = None


class OperatorPasswordResetRequest(BaseModel):
    password: str = Field(..., min_length=10, max_length=10)


class TrackerTicketListStats(BaseModel):
    avg_rating: Optional[float] = None
    avg_rating_mine: Optional[float] = None


class TrackerTicketListResponse(BaseModel):
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    items: list[TrackerTicketListItem]
    stats: Optional[TrackerTicketListStats] = None


class TrackerTicketListDigestResponse(BaseModel):
    """Лёгкий поллинг списка: changed=false — полный /list не нужен."""
    changed: bool = True
    digest: str
    total: int = 0


class DeskSearchSubscriberHit(BaseModel):
    id: int
    login: str
    name: str
    email: str | None = None
    phone: str | None = None
    id_doc: str | None = None
    is_juridical: int = 0
    station_id: int | None = None
    hotspot_id: int | None = None


_RU_PHONE_RE = re.compile(r"^\+7\d{10}$")


def _normalize_ru_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone.strip())
    if digits.startswith("8") and len(digits) == 11:
        digits = f"7{digits[1:]}"
    if digits.startswith("7") and len(digits) == 11:
        return f"+7{digits[1:]}"
    raise ValueError("Телефон в формате +7XXXXXXXXXX (10 цифр после +7)")


class ConnectionLeadPayload(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    phone: str = Field(..., min_length=12, max_length=12)
    potential_subscribers: int | None = Field(
        None,
        ge=0,
        le=99_999,
        description="Только для нового партнёра",
    )
    sees_network: bool | None = Field(
        None,
        description="Новый абонент: видит ли сеть на месте",
    )
    plans_new_station: bool | None = Field(
        None,
        description="Новый партнёр: планирует ли станцию",
    )
    notes: str | None = Field(None, max_length=2000, description="Дополнительно от звонящего")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        normalized = _normalize_ru_phone(v)
        if not _RU_PHONE_RE.match(normalized):
            raise ValueError("Телефон в формате +7XXXXXXXXXX (10 цифр после +7)")
        return normalized


class RegisterCallRequest(BaseModel):
    connection_kind: str = Field(
        "existing",
        description="existing | new_subscriber | new_partner",
    )
    body: str | None = Field(
        None,
        max_length=8000,
        description="Что говорит клиент (только для existing)",
    )
    user_id: int | None = Field(None, description="ID абонента (только для existing)")
    lead: ConnectionLeadPayload | None = Field(
        None,
        description="Анкета нового подключения (new_subscriber / new_partner)",
    )
    station_id: int | None = None
    hotspot_id: int | None = None

    @model_validator(mode="after")
    def validate_connection_kind(self) -> "RegisterCallRequest":
        kind = (self.connection_kind or "existing").strip()
        if kind not in ("existing", "new_subscriber", "new_partner"):
            raise ValueError("Некорректный тип обращения")
        self.connection_kind = kind

        if kind == "existing":
            if self.user_id is None:
                raise ValueError("Выберите абонента")
            if not (self.body or "").strip():
                raise ValueError("Опишите, что говорит клиент")
            return self

        if self.lead is None:
            raise ValueError("Заполните анкету нового подключения")
        if kind == "new_subscriber" and self.lead.sees_network is None:
            raise ValueError("Укажите, видит ли клиент сеть")
        if kind == "new_partner" and self.lead.plans_new_station is None:
            raise ValueError("Укажите, планирует ли партнёр новую станцию")
        if (
            kind == "new_partner"
            and self.lead.plans_new_station is True
            and self.lead.potential_subscribers is None
        ):
            raise ValueError("Укажите число потенциальных абонентов")
        return self


class RegisterCallResponse(BaseModel):
    id: int


class LinkTicketSubscriberRequest(BaseModel):
    user_id: int = Field(..., ge=1, description="ID выбранного абонента")


class TransferTicketToEngineersRequest(BaseModel):
    category_id: int | None = Field(
        None,
        ge=1,
        description="ID подкатегории (не используется операторами КС; для совместимости API)",
    )
    comment: str | None = Field(
        None,
        max_length=8000,
        description="Комментарий при передаче инженерам (необязательно)",
    )


class CloseTicketRequest(BaseModel):
    category_id: int = Field(..., ge=1, description="ID подкатегории (лист ticket_categories)")
    comment: str | None = Field(
        None,
        max_length=8000,
        description="Комментарий при закрытии (необязательно)",
    )


class DeskSearchKbHit(BaseModel):
    """Заглушка под будущий поиск по базе знаний."""

    id: int
    title: str
    excerpt: str | None = None


class DeskSearchResponse(BaseModel):
    subscribers: list[DeskSearchSubscriberHit]
    kb: list[DeskSearchKbHit] = []


class TicketAttachmentItem(BaseModel):
    id: int
    file_path: str
    original_filename: str
    file_ext: str | None = None
    file_size_bytes: int | None = None
    is_image: bool = False


class TicketMessageReplyPreview(BaseModel):
    id: int
    author_name: str | None = None
    text: str = ""
    is_deleted: bool = False


class TicketMessageReadByItem(BaseModel):
    label: str
    read_at_iso: str


class TicketMessageItem(BaseModel):
    id: int
    side: str
    text: str
    created_at_iso: str | None = None
    has_read: bool = True
    author_name: str | None = None
    recipient_read_at_iso: str | None = None
    read_by: list[TicketMessageReadByItem] = Field(default_factory=list)
    reply_to_id: int | None = None
    is_edited: bool = False
    updated_at_iso: str | None = None
    reply_preview: TicketMessageReplyPreview | None = None
    legacy_file_url: str | None = None
    attachments: list[TicketAttachmentItem] = []
    is_initial: bool = False


class TicketMessageEditRequest(BaseModel):
    text: str = Field(..., min_length=0, max_length=20000)


class TicketDetailResponse(BaseModel):
    id: int
    title: str
    body: str | None = None
    status: str
    status_label: str
    is_open: bool
    priority: str | None = None
    priority_label: str | None = None
    support_line: int
    support_line_label: str
    queue_line: str = "cs"
    queue_line_label: str = "КС"
    action_by: str = "cs"
    action_by_label: str = "КС"
    chat_turn: str = "subscriber"
    chat_turn_label: str = "Ждём абонента"
    action_since_iso: str | None = None
    has_unread: bool = False
    list_highlight: str = "none"
    communication_state: str | None = None
    communication_label: str | None = None
    source: str
    source_label: str
    category_label: str | None = None
    category_name: str | None = None
    category_parent_name: str | None = None
    category_id: int | None = None
    category_parent_id: int | None = None
    user_id: int | None = None
    caller_name: str | None = None
    subscriber_name: str | None = None
    subscriber_display_name: str | None = None
    subscriber_login: str | None = None
    subscriber_online: bool = False
    subscriber_is_juridical: int = 0
    subscriber_profile_user_id: int | None = None
    assignee_label: str | None = None
    assignee_role: str | None = None
    assignee_is_viewer: bool = False
    assigned_to: int | None = None
    staff_participants: list[TicketStaffParticipant] = Field(default_factory=list)
    station_name: str | None = None
    station_id: int | None = None
    date_of_create_iso: str | None = None
    date_of_close_iso: str | None = None
    can_reopen: bool = False
    updated_at_iso: str | None = None
    assigned_at_iso: str | None = None
    chat_mode: str
    can_reply: bool = True
    subscriber_account: TicketSubscriberAccountSummary | None = None


class TicketPollSnapshot(BaseModel):
    """Снимок статуса тикета для поллинга сообщений (без тяжёлого detail)."""

    status: str
    status_label: str
    is_open: bool
    can_reopen: bool = False
    can_reply: bool = True
    date_of_close_iso: str | None = None
    updated_at_iso: str | None = None
    queue_line: str = "cs"
    queue_line_label: str = "КС"
    action_by: str = "cs"
    action_by_label: str = "КС"
    chat_turn: str = "subscriber"
    chat_turn_label: str = "Ждём абонента"
    action_since_iso: str | None = None
    list_highlight: str = "none"
    communication_state: str | None = None
    communication_label: str | None = None


class TicketMessagesResponse(BaseModel):
    messages: list[TicketMessageItem]
    chat_mode: str
    read_receipts: dict[int, str] = Field(default_factory=dict)
    read_by_receipts: dict[int, list[TicketMessageReadByItem]] = Field(default_factory=dict)
    has_older: bool = False
    has_newer: bool = False
    ticket: TicketPollSnapshot | None = None


class TicketReadReceiptsResponse(BaseModel):
    chat_mode: str
    read_receipts: dict[int, str] = Field(default_factory=dict)
    read_by_receipts: dict[int, list[TicketMessageReadByItem]] = Field(default_factory=dict)


class TicketMarkReadRequest(BaseModel):
    message_ids: list[int] = Field(default_factory=list)


class TicketCommentItem(BaseModel):
    id: int
    side: str
    text: str
    author_name: str
    is_me: bool = False
    created_at_iso: str | None = None
    is_edited: bool = False
    updated_at_iso: str | None = None


class TicketCommentsResponse(BaseModel):
    comments: list[TicketCommentItem]
    has_older: bool = False
    has_newer: bool = False


class TicketCommentEditRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class TicketCommentSendResponse(BaseModel):
    comment: TicketCommentItem


class TicketSendMessageResponse(BaseModel):
    message: TicketMessageItem | None = None
    messages: list[TicketMessageItem] | None = None

    @model_validator(mode="after")
    def require_any(self) -> "TicketSendMessageResponse":
        if self.message is None and not self.messages:
            raise ValueError("message or messages is required")
        return self


class TicketCategoryLeaf(BaseModel):
    """Подкатегория (parent_id IS NOT NULL)."""

    id: int
    name: str
    slug: str
    theme: str
    complexity: str
    priority: str
    priority_label: str
    support_line: int
    sla_minutes: int
    need_user_selection: bool = False
    need_station_selection: bool = False
    object_type: str | None = None


class TicketCategoryGroup(BaseModel):
    """Корневая группа (parent_id IS NULL)."""

    id: int
    name: str
    slug: str
    children: list[TicketCategoryLeaf] = Field(default_factory=list)


class TicketCategoriesResponse(BaseModel):
    catalog_source: str
    items: list[TicketCategoryGroup]


class HelpdeskMacroItem(BaseModel):
    id: int
    name: str
    message_text: str
    sort_order: int = 0


class HelpdeskMacrosResponse(BaseModel):
    items: list[HelpdeskMacroItem] = Field(default_factory=list)
