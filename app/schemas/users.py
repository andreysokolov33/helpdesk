from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class JuridicalAccountContractRow(BaseModel):
    """Строка в колонке договора УЗ: подпись + срок, опционально приглушённый (Сгенерирован)."""

    label: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    muted: bool = False


class UserInfo(BaseModel):
    id: int
    fullname: str
    tariff: Optional[str]
    tariff_sub: Optional[str] = None
    # no_tariff | frozen | limited | unlimited | unknown
    tariff_type: Optional[str] = None
    station: Optional[str]
    login: str
    email: Optional[str]
    mobtel: Optional[str]
    station_id: Optional[int] = None
    detail_formular_missing: bool = False


class UsersListResponse(BaseModel):
    users: List[UserInfo]
    total: int
    # stations: List[str]


class JuridicalAccountRow(BaseModel):
    id: int
    login: str
    balance: float
    archive: int = 0  # 1 — УЗ в архиве (users.user.archive)
    user_status: Optional[int] = None
    tariff: Optional[str] = None
    tariff_sub: Optional[str] = None
    tariff_type: Optional[str] = None
    station: Optional[str] = None
    station_id: Optional[int] = None
    # partner.diler.fullname по ip_group.id_diler
    partner_fullname: Optional[str] = None
    # Активное гарантийное письмо: users.privileged_users, date_end >= сегодня
    guarantee_letter_until: Optional[date] = None
    # Договоры по oss.contract_user_relation + oss.jur_contract_list
    contract_rows: List[JuridicalAccountContractRow] = Field(default_factory=list)


class OrganizationListItem(BaseModel):
    """Строка списка организаций (/users/list)."""

    id: int
    fullname: str
    user_count: int
    organization_is_active: bool = True
    accounts: List[JuridicalAccountRow] = Field(default_factory=list)
    tariff: Optional[str] = None
    tariff_sub: Optional[str] = None
    tariff_type: Optional[str] = None
    station: Optional[str] = None
    station_id: Optional[int] = None
    login: str = ""
    email: Optional[str] = None
    mobtel: Optional[str] = None
    detail_formular_missing: bool = False


class OrganizationsListResponse(BaseModel):
    organizations: List[OrganizationListItem]
    total: int


class JuridicalAccountsResponse(BaseModel):
    organization_name: str
    juridical_id: int
    accounts: List[JuridicalAccountRow]
