from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, Double, Enum, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

from app.database import Base


class Friend2friend(Base):
    __tablename__ = 'friend2friend'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9495143173_primary'),
        {'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    user_from = mapped_column(BigInteger, nullable=False)
    user_to = mapped_column(BigInteger, nullable=False)
    amount = mapped_column(Numeric(10, 2), nullable=False)
    date = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    ip_address = mapped_column(INET)


class IpgrpAndPaysystem(Base):
    __tablename__ = 'ipgrp_and_paysystem'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94895323_primary'),
        Index('ipgrp_and_paysystem_id_grp_idx', 'id_grp'),
        {'comment': 'Связь ID IP группы и ID платежной системы', 'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    id_grp = mapped_column(BigInteger)
    pay_grp = mapped_column(BigInteger)


class PartnersRewardHistory(Base):
    __tablename__ = 'partners_reward_history'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='partners_reward_history_pkey'),
        Index('idx_analytic_partners_reward_diler_id', 'diler_id'),
        Index('partners_reward_history_uq', 'yearmonth', 'diler_id', unique=True),
        {'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    yearmonth = mapped_column(Integer)
    partner = mapped_column(String)
    diler_id = mapped_column(BigInteger)
    phyz_skystream = mapped_column(Numeric)
    phyz_letatel = mapped_column(Numeric)
    jur_skystream = mapped_column(Numeric)
    jur_letatel = mapped_column(Numeric)
    total_skystream = mapped_column(Numeric)
    total_letatel = mapped_column(Numeric)
    total_pays = mapped_column(Numeric)
    nds = mapped_column(Numeric)
    total_pays_for_agents = mapped_column(Numeric)
    proc = mapped_column(Integer)
    agents = mapped_column(Numeric)


class Pays(Base):
    __tablename__ = 'pays'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94895_primary'),
        Index('pays_id_grp_idx', 'id_grp'),
        Index('pays_id_partner_idx', 'id_partner'),
        Index('pays_pay_iden_idx', 'pay_iden'),
        Index('pays_pay_iden_state_idx', 'pay_iden', 'state', unique=True),
        Index('pays_state_idx', 'state'),
        Index('pays_uid_idx', 'uid'),
        {'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    type = mapped_column(String(50), nullable=False, server_default=text("'cash'::character varying"))
    state = mapped_column(Enum('in', 'payed', 'canceled', 'refund', name='pays_state'), nullable=False, server_default=text("'in'::pays_state"))
    pay_iden = mapped_column(String(128), server_default=text('NULL::character varying'))
    amount = mapped_column(Double(53), server_default=text("'0'::double precision"))
    id_bill = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    pay_str = mapped_column(Text)
    date_in = mapped_column(BigInteger)
    date_pay = mapped_column(BigInteger)
    date_in_tz = mapped_column(DateTime(timezone=True), server_default=text('now()'))
    date_pay_tz = mapped_column(DateTime(timezone=True))
    date_state = mapped_column(BigInteger)
    comm = mapped_column(Text, comment='Данная колнка будет использоваться для идентификации кассы')
    prc = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    dt = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    id_partner = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    rrn = mapped_column(String(24), server_default=text('NULL::character varying'), comment='Для Сбербанка делали')
    orange = mapped_column(Integer, server_default=text('0'), comment='Пробит ли чек в Orange. 0 - нет, 1 - да')
    uid = mapped_column(Integer, comment='ID абонента, чтобы не лезть в pays_bills')
    id_grp = mapped_column(Integer, comment='Привязка платежа к IP группе абонента')
    bort = mapped_column(Integer, comment='Это ID Hotspot')
    received = mapped_column(Boolean, server_default=text('false'))


class PaysBills(Base):
    __tablename__ = 'pays_bills'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90754_primary'),
        Index('pays_bills_external_id_idx', 'external_id'),
        Index('pays_bills_id_user_idx', 'id_user'),
        Index('pays_bills_system_idx', 'system'),
        Index('pays_bills_type_idx', 'type'),
        {'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    type = mapped_column(String(16), nullable=False)
    system = mapped_column(String(30), nullable=False, server_default=text("'normal'::character varying"))
    payed = mapped_column(String(1), nullable=False, server_default=text("'0'::character varying"))
    id_user = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    amount = mapped_column(Double(53))
    datum = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    external_id = mapped_column(String(255), server_default=text('NULL::character varying'))
    order_id = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    date = mapped_column(BigInteger)
    vno = mapped_column(BigInteger)
    id_grp = mapped_column(BigInteger)
    created_by = mapped_column(BigInteger, comment='Кто внёс запись (users.abs_users.id)')
    create_date = mapped_column(DateTime(True), comment='Момент зачисления (timestamptz)')


class PaysSystems(Base):
    __tablename__ = 'pays_systems'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94895324_primary'),
        {'schema': 'payments'}
    )

    id = mapped_column(BigInteger)
    pay_name = mapped_column(String(50))
    rus_name = mapped_column(String, nullable=True)
    for_skystream = mapped_column(Boolean, nullable=False, server_default=text('false'))
    for_datelecom = mapped_column(Boolean, nullable=False, server_default=text('false'))
    active = mapped_column(Boolean, nullable=False, server_default=text('true'))


class PaymentsPayment(Base):
    __tablename__ = 'payments_payment'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='payments_payment_pkey'),
        {'schema': 'payments'}
    )

    id = mapped_column(Integer)
    amount = mapped_column(Double(53), nullable=False)
    payment_system = mapped_column(String(50), nullable=False)
    user_id = mapped_column(Integer)
    status = mapped_column(String(20))
    transaction_id = mapped_column(String(255))
    created_at = mapped_column(DateTime)
    updated_at = mapped_column(DateTime)
