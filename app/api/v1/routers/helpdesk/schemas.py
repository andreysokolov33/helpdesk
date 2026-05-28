from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.api.v1.routers.helpdesk.user_profile_schemas import TicketSubscriberAccountSummary


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
    assignee_name: Optional[str] = None
    assignee_role: Optional[str] = None
    assignee_is_viewer: bool = False
    """True, если тикет назначен на текущего оператора (users.skystream_users.id)."""
    has_unread: bool = False
    """Есть сообщения абонента, которые ещё не прочитал ни один сотрудник."""
    communication_state: Optional[str] = None
    """needs_reply | awaiting_subscriber"""
    communication_label: Optional[str] = None
    date_of_create: datetime
    updated_at: Optional[datetime] = None


class TrackerTicketListResponse(BaseModel):
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    items: list[TrackerTicketListItem]


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


class RegisterCallRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000, description="Что говорит клиент")
    user_id: int | None = Field(None, description="ID абонента; NULL если не определён")
    subscriber_unknown: bool = Field(
        False,
        description="Абонент не определён — user_id не передаётся, person_type=cs",
    )
    caller_name: str | None = Field(
        None,
        max_length=500,
        description="Как представился звонящий, если абонент не в базе",
    )
    station_id: int | None = None
    hotspot_id: int | None = None

    @model_validator(mode="after")
    def require_caller_when_unknown(self) -> "RegisterCallRequest":
        if self.subscriber_unknown and not (self.caller_name or "").strip():
            raise ValueError("Укажите, как представился клиент")
        return self


class RegisterCallResponse(BaseModel):
    id: int


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


class TicketMessageItem(BaseModel):
    id: int
    side: str
    text: str
    created_at_iso: str | None = None
    has_read: bool = True
    author_name: str | None = None
    recipient_read_at_iso: str | None = None
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
    source: str
    source_label: str
    category_label: str | None = None
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
    assignee_name: str | None = None
    assignee_role: str | None = None
    assignee_is_viewer: bool = False
    station_name: str | None = None
    station_id: int | None = None
    date_of_create_iso: str | None = None
    updated_at_iso: str | None = None
    assigned_at_iso: str | None = None
    chat_mode: str
    can_reply: bool = True
    subscriber_account: TicketSubscriberAccountSummary | None = None


class TicketMessagesResponse(BaseModel):
    messages: list[TicketMessageItem]
    chat_mode: str
    read_receipts: dict[int, str] = Field(default_factory=dict)
    has_older: bool = False
    has_newer: bool = False


class TicketMarkReadRequest(BaseModel):
    message_ids: list[int] = Field(default_factory=list)


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
