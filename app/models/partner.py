from typing import List

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Text, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

from app.database import Base


class ChangePasswordLog(Base):
    __tablename__ = 'change_password_log'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9030477_primary'),
        {'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    partner_id = mapped_column(BigInteger, nullable=False)
    old_password = mapped_column(String(50), nullable=False)
    new_password = mapped_column(String(50), nullable=False)
    created_at = mapped_column(
        DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    ip_address = mapped_column(INET)


class Diler(Base):
    __tablename__ = 'diler'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90304_primary'),
        {'comment': 'Customers', 'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    login = mapped_column(String(40), nullable=False)
    password = mapped_column(String(50), nullable=False)
    tel = mapped_column(String(128), nullable=False)
    mail = mapped_column(String(128), nullable=False)
    sogl = mapped_column(String(128), nullable=False)
    sogl_date = mapped_column(
        String(56), nullable=False, server_default=text("''::character varying"))
    name = mapped_column(String(256), nullable=False)
    name_podp = mapped_column(String(256), nullable=False)
    fullname = mapped_column(String(256), nullable=False)
    rod = mapped_column(String(256), nullable=False)
    inn = mapped_column(String(256), nullable=False,
                        server_default=text("''::character varying"))
    kpp = mapped_column(String(256), nullable=False)
    img = mapped_column(String(500), nullable=False)
    proc = mapped_column(BigInteger)
    proc_case = mapped_column(Text)
    id_parent = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    jur_type = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    remember_token = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    host = mapped_column(
        String(128), server_default=text('NULL::character varying'))
    last_login = mapped_column(DateTime(True))
    nds = mapped_column(Boolean)
    ogrn = mapped_column(String(256))
    address = mapped_column(Text)
    bank = mapped_column(String(256))
    bik = mapped_column(String(256))
    rs = mapped_column(String(256), comment='Расчетный счет')
    ks = mapped_column(String(256))
    position_of_signatory = mapped_column(
        String(256), comment='Должность подписанта')
    fio_of_signatory = mapped_column(String(256), comment='ФИО подписанта')
    active = mapped_column(Boolean, server_default=text('true'))
    has_form = mapped_column(Boolean, server_default=text('true'))
    fix_proc = mapped_column(Boolean, server_default=text('false'))
    global_id = mapped_column(BigInteger)


class LkAuth(Base):
    __tablename__ = 'lk_auth'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9042346_primary'),
        {'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(BigInteger)
    date = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    ip = mapped_column(String(24))
    success = mapped_column(Boolean, server_default=text(
        'true'), comment='Успешная или нет авторизация')
    person_type = mapped_column(String(32), nullable=True, comment='partner | technician')


class LkTokens(Base):
    __tablename__ = 'lk_tokens'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='partner_tokens_pkey'),
        {'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(Integer, nullable=False)
    token = mapped_column(String(255), nullable=False)
    create_date = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    canceled_date = mapped_column(DateTime, server_default=text("(CURRENT_TIMESTAMP + '30 days'::interval)"))
    ip_address = mapped_column(String(45))


class PartnerDocuments(Base):
    __tablename__ = 'partner_documents'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90689_primary'),
        {'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    section = mapped_column(String(100), nullable=False)
    title = mapped_column(String(100), nullable=False)
    url_doc = mapped_column(String(100), nullable=False)
    explanation = mapped_column(
        String(100), server_default=text('NULL::character varying'))


class PartnerNews(Base):
    __tablename__ = 'partner_news'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90695_primary'),
        {'schema': 'partner'}
    )

    id = mapped_column(BigInteger)
    title_name = mapped_column(String(200), nullable=False)
    context = mapped_column(String(5000), nullable=False)
    is_important = mapped_column(Integer, nullable=False)
    author = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    date = mapped_column(DateTime(True))


class SupportProposals(Base):
    __tablename__ = 'support_proposals'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='support_proposals_pkey'),
        Index('idx_proposals_created_at', 'created_at'),
        Index('idx_proposals_status', 'status'),
        Index('idx_proposals_user_id', 'user_id'),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer)
    title = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=False)
    status = mapped_column(String(50), nullable=False, server_default=text(
        "'На обсуждении'::character varying"))
    priority = mapped_column(String(20), nullable=False,
                             server_default=text("'Средний'::character varying"))
    category = mapped_column(String(100), nullable=False,
                             server_default=text("'Общее'::character varying"))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    user_id = mapped_column(Integer, nullable=False)

    support_messages: Mapped[List['SupportMessages']] = relationship(
        'SupportMessages', uselist=True, back_populates='proposal')


class UserActions(Base):
    __tablename__ = 'user_actions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_actions_pkey'),
        Index('idx_user_actions_page_path', 'page_path'),
        Index('idx_user_actions_target_user_id', 'target_user_id'),
        Index('idx_user_actions_timestamp', 'timestamp'),
        Index('idx_user_actions_user_id', 'user_id'),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer)
    user_id = mapped_column(Integer, nullable=False)
    page_path = mapped_column(Text, nullable=False)
    timestamp = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    target_user_id = mapped_column(Integer)
    action_type = mapped_column(Text)
    action_detail = mapped_column(Text)
    person_type = mapped_column(String(32), nullable=True, comment='partner | technician')


class SupportMessages(Base):
    __tablename__ = 'support_messages'
    __table_args__ = (
        ForeignKeyConstraint(['proposal_id'], ['partner.support_proposals.id'],
                             ondelete='CASCADE', name='support_messages_proposal_id_fkey'),
        PrimaryKeyConstraint('msg_id', name='support_messages_pkey'),
        Index('idx_messages_proposal_id_date', 'proposal_id', 'date'),
        {'schema': 'partner'}
    )

    msg_id = mapped_column(Integer)
    proposal_id = mapped_column(Integer, nullable=False)
    text_ = mapped_column('text', Text, nullable=False)
    user_id = mapped_column(Integer, nullable=False)
    date = mapped_column(DateTime(True), nullable=False,
                         server_default=text('now()'))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(True))

    proposal: Mapped['SupportProposals'] = relationship(
        'SupportProposals', back_populates='support_messages')
    message_attachments: Mapped[List['MessageAttachments']] = relationship(
        'MessageAttachments', uselist=True, back_populates='message')


class MessageAttachments(Base):
    __tablename__ = 'message_attachments'
    __table_args__ = (
        ForeignKeyConstraint(['message_id'], ['partner.support_messages.msg_id'],
                             ondelete='CASCADE', name='message_attachments_message_id_fkey'),
        PrimaryKeyConstraint('id', name='message_attachments_pkey'),
        Index('idx_attachments_message_id', 'message_id'),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer)
    message_id = mapped_column(Integer, nullable=False)
    file_path = mapped_column(String(500), nullable=False)
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    file_name = mapped_column(String(255))
    mime_type = mapped_column(String(100))

    message: Mapped['SupportMessages'] = relationship(
        'SupportMessages', back_populates='message_attachments')


class TaxData(Base):
    __tablename__ = 'tax_data'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tax_data_pkey'),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer)
    percentage = mapped_column(
        Integer, nullable=False, comment='Percentage value')
    amount = mapped_column(BigInteger, nullable=False,
                           comment='Amount in currency')


class Technician(Base):
    __tablename__ = 'technicians'
    __table_args__ = (
        PrimaryKeyConstraint('technician_id', name='technicians_pkey'),
        {'schema': 'partner'}
    )

    technician_id = mapped_column(Integer, autoincrement=True)
    login = mapped_column(String(50), nullable=False)
    password = mapped_column(String(255), nullable=False)
    full_name = mapped_column(String(100), nullable=False)
    phone_number = mapped_column(String(20))
    is_active = mapped_column(Boolean, server_default=text('true'))
    created_at = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))


class TechnicianStation(Base):
    __tablename__ = 'technician_stations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='technician_stations_pkey'),
        ForeignKeyConstraint(
            ['technician_id'], ['partner.technicians.technician_id'],
            ondelete='CASCADE', name='technician_stations_technician_id_fkey'
        ),
        ForeignKeyConstraint(
            ['station_id'], ['wifitochka.ip_group.id'],
            ondelete='CASCADE', name='technician_stations_station_id_fkey'
        ),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer, autoincrement=True)
    technician_id = mapped_column(Integer, nullable=False)
    station_id = mapped_column(Integer, nullable=False)
    assigned_date = mapped_column(DateTime(True), server_default=text('now()'))


class TechnicianPartner(Base):
    __tablename__ = 'technicians_partners'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='technicians_partners_pkey'),
        ForeignKeyConstraint(
            ['partner_id'], ['partner.diler.id'],
            ondelete='CASCADE', name='technicians_partners_partner_id_fkey'
        ),
        ForeignKeyConstraint(
            ['technician_id'], ['partner.technicians.technician_id'],
            ondelete='CASCADE', name='technicians_partners_technician_id_fkey'
        ),
        {'schema': 'partner'}
    )

    id = mapped_column(Integer, autoincrement=True)
    partner_id = mapped_column(Integer, nullable=False)
    technician_id = mapped_column(Integer, nullable=False)
    assigned_date = mapped_column(DateTime(True), server_default=text('now()'))
