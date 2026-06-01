from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProfilePersonal(BaseModel):
    user_id: int
    name: str
    login: str
    email: Optional[str] = None
    phone: Optional[str] = None
    id_doc: Optional[str] = None
    is_juridical: int
    entity_label: str
    user_status: Optional[int] = None
    status_label: str
    station_name: Optional[str] = None
    auth_page: Optional[str] = None


class ProfileOnline(BaseModel):
    is_online: bool
    last_session_end: Optional[datetime] = None
    last_session_end_label: Optional[str] = None


class ProfileTariffActive(BaseModel):
    state: Literal["active", "inactive", "frozen", "planned_freeze", "ended"]
    tariff_name: str
    real_type: Optional[str] = None
    is_active: bool
    rate_up: str = "—"
    rate_down: str = "—"
    speed_unlimited: bool = False
    remain_traffic_mb: float = 0
    full_packet_mb: float = 0
    jur_main_packet_mb: Optional[float] = None
    jur_dop_packet_mb: Optional[float] = None
    overrun_mb: Optional[float] = None
    traffic_renew_count: Optional[int] = None
    msk_reset: Optional[str] = None
    local_reset: Optional[str] = None
    last_traffic_reset_label: Optional[str] = None
    valid_date_label: Optional[str] = None
    disconnect_at_label: Optional[str] = None
    remaining_label: Optional[str] = None
    planned_freeze_at: Optional[str] = None
    frozen_at: Optional[str] = None
    unfreeze_at: Optional[str] = None
    frozen_remaining_label: Optional[str] = None
    freeze_reason: Optional[str] = None
    can_freeze: bool = False
    can_unfreeze: bool = False
    can_cancel_planned_freeze: bool = False
    can_remove_ended_tariff: bool = False
    can_disconnect_sessions: bool = True


class ProfileTicket(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    category_theme: Optional[str] = None
    date_of_create: datetime
    date_of_close: Optional[datetime] = None
    assigned_to_role: Optional[str] = None
    support_line: int
    support_line_label: str
    status: str
    status_label: str


class ProfileHealthCheck(BaseModel):
    items: list[str] = Field(default_factory=list)


class TicketSubscriberTariffSummary(BaseModel):
    """Краткая информация о тарифе для сайдбара тикета."""

    connected: bool = False
    """Есть подключенный тариф в radusergroup / freeze."""
    state: str = "none"
    """none | active | frozen | planned_freeze | inactive | ended — для бейджа в UI."""
    tariff_name: Optional[str] = None
    status_label: str = "Не подключен"
    type_label: Optional[str] = None
    frozen_at_label: Optional[str] = None
    unfreeze_at_label: Optional[str] = None
    frozen_remaining_label: Optional[str] = None
    remain_traffic_mb: Optional[float] = None
    full_packet_mb: Optional[float] = None
    jur_main_packet_mb: Optional[float] = None
    jur_dop_packet_mb: Optional[float] = None
    overrun_mb: Optional[float] = None
    rate_up: Optional[str] = None
    rate_down: Optional[str] = None
    msk_reset: Optional[str] = None
    local_reset: Optional[str] = None
    valid_date_label: Optional[str] = None
    """Дата окончания тарифа (МСК), из user_service_date.valid_date."""
    remaining_label: Optional[str] = None
    """Остаток срока: «осталось N дн HH:MM»."""


class TicketSubscriberAccountSummary(BaseModel):
    balance: float = 0
    tariff: TicketSubscriberTariffSummary = Field(default_factory=TicketSubscriberTariffSummary)


class ProfileTicketListResponse(BaseModel):
    total: int = 0
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    items: list[ProfileTicket] = Field(default_factory=list)


class PaymentHistoryItem(BaseModel):
    msk_date: datetime
    msk_date_label: str
    state: str
    state_label: str
    payment_type: str
    type_label: str
    amount: float


class PaymentHistoryListResponse(BaseModel):
    total: int = 0
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    items: list[PaymentHistoryItem] = Field(default_factory=list)


class TariffHistoryItem(BaseModel):
    activated_at: datetime
    activated_at_label: str
    row_kind: Literal["tariff", "dop"]
    type_label: str
    type_hint: Optional[str] = None
    active_tariff: bool = False
    deactivation_at_label: Optional[str] = None
    price: Optional[float] = None
    price_label: str


class TariffHistoryListResponse(BaseModel):
    total: int = 0
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    items: list[TariffHistoryItem] = Field(default_factory=list)


class UserProfileResponse(BaseModel):
    personal: ProfilePersonal
    online: ProfileOnline
    open_sessions_count: int = 0
    balance: float
    tariff: Optional[ProfileTariffActive] = None
    netflow_note: Optional[str] = None
    netflow_tariff: Optional[str] = None
    health_check: ProfileHealthCheck = Field(default_factory=ProfileHealthCheck)
    tickets: ProfileTicketListResponse = Field(default_factory=ProfileTicketListResponse)
    disconnect_sessions_remaining: int = 2
    disconnect_sessions_limit: int = 2
    disconnect_sessions_window_minutes: int = 30


class FreezeRequest(BaseModel):
    date_freeze: Optional[datetime] = None
    date_unfreeze: Optional[datetime] = None


class ActionMessage(BaseModel):
    ok: bool = True
    message: str


class TariffBlockResponse(BaseModel):
    """Блок тарифа на карточке абонента (после отключения — без перезагрузки страницы)."""

    ok: bool = True
    message: str
    tariff: Optional[ProfileTariffActive] = None
    netflow_note: Optional[str] = None
    netflow_tariff: Optional[str] = None
    health_check: ProfileHealthCheck = Field(default_factory=ProfileHealthCheck)
