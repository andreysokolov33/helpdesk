from datetime import datetime
from typing import Optional
import uuid as _uuid

from sqlalchemy import (
    BigInteger, Boolean, CHAR, Date, DateTime, Double, ForeignKey, Numeric,
    ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint,
    Sequence, SmallInteger, String, Text, UniqueConstraint, Uuid, text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JurBlankOrderList(Base):
    __tablename__ = 'jur_blank_order_list'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90590_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('oss_jur_blank_order_list_1_id_seq', schema='oss'))
    number_contract = mapped_column(String(15), server_default=text('NULL::character varying'))
    type_tariff = mapped_column(CHAR(30), server_default=text('NULL::bpchar'))
    size_tariff = mapped_column(String(15), server_default=text("'0'::character varying"))
    name_tariff = mapped_column(String(100), server_default=text('NULL::character varying'))
    id_account_abc = mapped_column(String(8), server_default=text('NULL::character varying'))
    status = mapped_column(String(30), server_default=text('NULL::character varying'))
    date_start_blank_order = mapped_column(CHAR(10), server_default=text('NULL::bpchar'))
    date_end_blank_order = mapped_column(CHAR(10), server_default=text('NULL::bpchar'))
    number_blank_order = mapped_column(CHAR(10), server_default=text('NULL::bpchar'))
    number_canel_blank_order = mapped_column(CHAR(10), server_default=text('NULL::bpchar'))
    additional_traffic = mapped_column(SmallInteger, server_default=text("'0'::smallint"))
    type_order = mapped_column(String(100), server_default=text('NULL::character varying'))
    contract_cost = mapped_column(Double(53))
    traffic_dop_price = mapped_column(Double(53), server_default=text("'0'::double precision"))
    speed_in_forward_channel = mapped_column(Integer)
    speed_in_reverse_channel = mapped_column(Integer)
    limited_speed_in_channel = mapped_column(Integer)
    xml_file = mapped_column(Text)
    login_account_abc = mapped_column(String(100), server_default=text('NULL::character varying'))
    castom = mapped_column(SmallInteger, server_default=text("'0'::smallint"))
    contract_id = mapped_column(
        BigInteger,
        ForeignKey('oss.jur_contract_list.id', ondelete='CASCADE'),
        nullable=True,
    )
    user_id = mapped_column(
        BigInteger,
        ForeignKey('users.user.id', ondelete='CASCADE'),
        nullable=True,
    )
    number_blank_order_int = mapped_column(Integer, nullable=True)
    url = mapped_column(Text, nullable=True)
    canceled_blank_number = mapped_column(Integer, nullable=True)
    date_from = mapped_column(Date, nullable=True)
    date_to = mapped_column(Date, nullable=True)
    packet_size = mapped_column(BigInteger, nullable=True)
    has_ip = mapped_column(Boolean, nullable=True, server_default=text("false"))
    ip_cost = mapped_column(Numeric(5, 2), nullable=True, server_default=text("0"))


class JurClientList(Base):
    __tablename__ = 'jur_client_list'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90621_primary'),
        ForeignKeyConstraint(
            ['vno_id'],
            ['wifitochka.virtual_network_operator.id'],
            ondelete='SET NULL',
            name='fk_jur_client_list_vno_id',
        ),
        ForeignKeyConstraint(
            ['partner_id'],
            ['partner.diler.id'],
            ondelete='SET NULL',
            name='fk_jur_client_list_partner_id',
        ),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('oss_jur_client_list_id_seq', schema='oss'))
    name_organization = mapped_column(Text)
    short_name_organization = mapped_column(Text)
    email_organization = mapped_column(String(150), server_default=text('NULL::character varying'))
    phone_organization = mapped_column(String(16), server_default=text('NULL::character varying'))
    addr_organization = mapped_column(Text)
    inn = mapped_column(String(20), server_default=text('NULL::character varying'))
    kpp = mapped_column(String(20), server_default=text('NULL::character varying'))
    ogrn = mapped_column(String(20), server_default=text('NULL::character varying'))
    bik = mapped_column(String(20), server_default=text('NULL::character varying'))
    bank = mapped_column(String(200), server_default=text('NULL::character varying'))
    correspondent_account = mapped_column(String(20), server_default=text('NULL::character varying'))
    current_account = mapped_column(String(20), server_default=text('NULL::character varying'))
    basis = mapped_column(String(500), server_default=text('NULL::character varying'))
    name_client = mapped_column(String(100), server_default=text('NULL::character varying'))
    post = mapped_column(String(100), server_default=text('NULL::character varying'))
    partner = mapped_column(CHAR(100), server_default=text('NULL::bpchar'))
    station = mapped_column(String(100), server_default=text('NULL::character varying'))
    id_valid_contract = mapped_column(String(100), server_default=text('NULL::character varying'))
    dop_phone_organization = mapped_column(String(100), server_default=text('NULL::character varying'))
    organization_pertain = mapped_column(Text, nullable=False)
    vno_id = mapped_column(BigInteger)
    partner_id = mapped_column(BigInteger)
    is_active = mapped_column(Boolean, server_default=text('true'))


class JurContractList(Base):
    __tablename__ = 'jur_contract_list'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90644_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('oss_jur_contract_list_id_seq', schema='oss'))
    short_name_organization = mapped_column(Text, nullable=False)
    comp = mapped_column(String(100), nullable=False)
    number_contract = mapped_column(String(20), server_default=text('NULL::character varying'))
    date_contract = mapped_column(CHAR(10), server_default=text('NULL::bpchar'))
    status = mapped_column(String(30), server_default=text('NULL::character varying'))
    xml_file = mapped_column(Text)
    castom = mapped_column(SmallInteger, server_default=text("'0'::smallint"))
    jur_id = mapped_column(String(8), server_default=text('NULL::character varying'))
    vno_id = mapped_column(BigInteger, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=True, server_default=text('CURRENT_TIMESTAMP'))
    effective_date = mapped_column(Date, nullable=True)
    valid_from = mapped_column(Date, nullable=True)
    valid_to = mapped_column(Date, nullable=True)
    juridical_id = mapped_column(BigInteger, nullable=True)
    contract_url = mapped_column(Text, nullable=True)
    contract_year = mapped_column("year", Integer, nullable=True)
    contract_seq_num = mapped_column("number", Integer, nullable=True)
    first_letter = mapped_column(String(10), nullable=True)
    last_letter = mapped_column(String(10), nullable=True)


class NoteHistory(Base):
    """Заметки по организации (oss.note_history). FK на users.abs_users в DDL не объявляем в ORM."""

    __tablename__ = 'note_history'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91282_primary'),
        Index('idx_note_history_juridical_id', 'juridical_id'),
        {'schema': 'oss'},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    name_org: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name_admin: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("''"))
    juridical_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    author_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)


class JurMonthlyBill(Base):
    __tablename__ = 'jur_monthly_bill'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90421_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger)
    account_id = mapped_column(BigInteger, nullable=False, comment='Идентификатор УЗ')
    contract = mapped_column(String(60), nullable=False, comment='Договор (Может меняться)')
    tariff_limit = mapped_column(Boolean, nullable=False, comment='0 Безлимитный\r\n1 Лимитный')
    tariff_extra = mapped_column(Boolean, nullable=False, comment='0 Без доп.трафика\r\n1 С доп.трафиком')
    tariff_volume = mapped_column(BigInteger, nullable=False, comment='Объём тарифа')
    date = mapped_column(String(6), nullable=False, comment='Период')
    month_start_balance = mapped_column(Double(53), nullable=False, comment='Баланс на начало месяца')
    jur_id = mapped_column(BigInteger, comment='Идентификатор ЮЛ')
    cost = mapped_column(Double(53), comment='Цена тарифа (Может меняться)')
    without_bill = mapped_column(Boolean, comment='1 Отказаться от создания счёта')
    editable = mapped_column(BigInteger, comment='0 В перерасчёте можно менять договор\r\n1 В перерасчёте можно менять договор и цену тарифа')
    creation = mapped_column(DateTime(True), comment='Дата создания записи')
    last_update = mapped_column(DateTime, comment='Время последнего апдейта строки, должно каждый день обновляться')
    balance = mapped_column(Double(53), comment='Это чистый баланс абонента перед выполнением всех  операций над строкой (взято просто из users.user). Это значение ДО списания доп трафика и прочих операций')
    last_change = mapped_column(DateTime, comment='Время последнего изменения данной строки. Например, параметры тарифа поменялись в середине месяца. Если изменений нет, то не меняется предыдущее значение')
    active_row = mapped_column(Boolean, server_default=text('true'), comment='Бывают случаи, когда на 1е число есть тариф у ЮЛ, но он не мог пользоваться услугой, поэтому просят удалить ез расписания запись. Чтобы не удалять из этой таблицы запись, просто ACTIVE = 0 выставлять будем, а ACTIVE = 1 всем активным')


class JurMonthlyBillV2(Base):
    """Месячный снимок: баланс на начало месяца (oss.jur_monthly_bill_v2)."""

    __tablename__ = 'jur_monthly_bill_v2'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='jur_monthly_bill_v2_pkey'),
        UniqueConstraint('user_id', 'year', 'month', name='uk_jur_monthly_bill_v2_user_year_month'),
        {'schema': 'oss'},
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    user_id = mapped_column(BigInteger, nullable=False)
    year = mapped_column('year', Integer, nullable=False)
    month = mapped_column('month', Integer, nullable=False)
    balance_value = mapped_column(Numeric(15, 2), nullable=False)
    is_active = mapped_column(Boolean, nullable=False, server_default=text('true'))
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))


class TariffConstructor(Base):
    __tablename__ = 'tariff_constructor'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_913182_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('tariff_constructor_new_id_seq', schema='oss'))
    sputnik = mapped_column(String(10), nullable=False)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53), nullable=False)
    extra_cost = mapped_column(Double(53), nullable=False)
    speed_in_forward_channel = mapped_column(Integer)
    speed_in_reverse_channel = mapped_column(Integer)
    satellite = mapped_column(Integer)
    plan_id = mapped_column(BigInteger)
    speed_forward_kb = mapped_column(Integer, nullable=True, comment='Скорость в прямом канале в Кбит/с')
    speed_reverse_kb = mapped_column(Integer, nullable=True, comment='Скорость в обратном канале в Кбит/с')


class TariffConstructorOld(Base):
    __tablename__ = 'tariff_constructor_old'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91312_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('tariff_constructor_id_seq', schema='oss'))
    sputnik = mapped_column(String(10), nullable=False)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53), nullable=False)
    extra_cost = mapped_column(Double(53), nullable=False)
    speed_in_forward_channel = mapped_column(Integer)
    speed_in_reverse_channel = mapped_column(Integer)


class TariffConstructorSpecial(Base):
    __tablename__ = 'tariff_constructor_special'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_913121_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(BigInteger, nullable=False)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53), nullable=False)
    extra_cost = mapped_column(Double(53), nullable=False)
    speed_in_forward_channel = mapped_column(Integer)
    speed_in_reverse_channel = mapped_column(Integer)


class TariffConstructorUnlim(Base):
    __tablename__ = 'tariff_constructor_unlim'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_913167_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('tariff_constructor_unlim_new_id_seq', schema='oss'))
    sputnik = mapped_column(String(10), nullable=False)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53))
    name_tariff = mapped_column(String(100), server_default=text('NULL::character varying'))
    limited_speed_in_forward_channel = mapped_column(Integer)
    limited_speed_in_reverse_channel = mapped_column(Integer)
    unlimited_speed_in_forward_channel = mapped_column(Integer)
    unlimited_speed_in_reverse_channel = mapped_column(Integer)
    satellite = mapped_column(Integer)
    plan_id = mapped_column(BigInteger)


class TariffConstructorUnlimOld(Base):
    __tablename__ = 'tariff_constructor_unlim_old'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91317_primary'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger, Sequence('tariff_constructor_unlim_id_seq', schema='oss'))
    sputnik = mapped_column(String(10), nullable=False)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53))
    name_tariff = mapped_column(String(100), server_default=text('NULL::character varying'))
    limited_speed_in_forward_channel = mapped_column(Integer)
    limited_speed_in_reverse_channel = mapped_column(Integer)
    unlimited_speed_in_forward_channel = mapped_column(Integer)
    unlimited_speed_in_reverse_channel = mapped_column(Integer)


class TariffConstructorPlan(Base):
    __tablename__ = 'tariff_constructor_plan'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tariff_constructor_plan_pkey'),
        {'schema': 'oss'}
    )

    id = mapped_column(BigInteger)
    plan_name = mapped_column(String(200), nullable=False)
    status = mapped_column(String(20), nullable=False, server_default=text("'draft'::character varying"))
    effective_from = mapped_column(DateTime(True))
    effective_to = mapped_column(DateTime(True))
    description = mapped_column(Text)
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class OssUserTokens(Base):
    """Таблица JWT-токенов OSS пользователей (oss.oss_user_tokens).

    FK к users.abs_users намеренно не объявлен в ORM — он существует в DDL,
    но users.abs_users живёт в отдельном MetaData, что вызывает NoReferencedTableError.
    """
    __tablename__ = 'oss_user_tokens'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='oss_user_tokens_pkey'),
        UniqueConstraint('refresh_jti', name='oss_user_tokens_refresh_jti_key'),
        UniqueConstraint('refresh_jti', 'is_revoked', name='unique_oss_active_refresh'),
        Index('ix_oss_user_tokens_access_jti', 'access_jti'),
        Index('ix_oss_user_tokens_refresh_jti', 'refresh_jti'),
        Index('ix_oss_user_tokens_user_active', 'user_id'),
        {'schema': 'oss'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    access_jti: Mapped[_uuid.UUID] = mapped_column(Uuid, nullable=False)
    refresh_jti: Mapped[_uuid.UUID] = mapped_column(Uuid, nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()')
    )
    access_expires_at: Mapped[DateTime] = mapped_column(DateTime(True), nullable=False)
    refresh_expires_at: Mapped[DateTime] = mapped_column(DateTime(True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True), nullable=True)


class UserLogsType(Base):
    """Справочник типов записей oss.user_logs_type."""

    __tablename__ = "user_logs_type"
    __table_args__ = {"schema": "oss"}

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class UserLog(Base):
    """Журнал действий oss.user_logs (FK в DDL на abs_users и user_logs_type)."""

    __tablename__ = "user_logs"
    __table_args__ = {"schema": "oss"}

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    author: Mapped[int] = mapped_column(BigInteger, nullable=False)
    log_type: Mapped[int] = mapped_column("type", Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
