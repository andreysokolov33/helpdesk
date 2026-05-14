from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    date_of_create: datetime
    updated_at: Optional[datetime] = None


class TrackerTicketListResponse(BaseModel):
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    items: list[TrackerTicketListItem]
