from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, Double, Enum, ForeignKey, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, Sequence, SmallInteger, String, Table, Text, UniqueConstraint, Uuid, func, text
from sqlalchemy.dialects.postgresql import CIDR, ENUM, INET, JSONB
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()
metadata = Base.metadata


class SkystreamUsers(Base):
    __tablename__ = 'skystream_users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='skystream_users_pkey'),
        UniqueConstraint('login', name='skystream_users_login_key'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    login = mapped_column(Text, nullable=False)
    email = mapped_column(Text)
    full_name = mapped_column(Text)
    password_hash = mapped_column(Text, nullable=False)
    role = mapped_column(Text, nullable=False,
                         server_default=text("'user'::text"))
    is_active = mapped_column(Boolean, nullable=False,
                              server_default=text('true'))
    is_superuser = mapped_column(
        Boolean, nullable=False, server_default=text('false'))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    last_login_at = mapped_column(DateTime(True))
    level = mapped_column(Integer)
    authored_reset_actions: Mapped[List['ResetTrafficAction']] = relationship(
        'ResetTrafficAction',
        back_populates='author'
    )


class SkystreamProjects(Base):
    __tablename__ = 'skystream_projects'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='projects_pkey'),
        UniqueConstraint('project_key', name='projects_project_key_key'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column('name', Text, nullable=False)
    project_key = mapped_column(Text, nullable=False)
    description = mapped_column(Text)
    is_active = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))


class SkystreamUserProjectAccess(Base):
    __tablename__ = 'skystream_user_project_access'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'project_id', name='user_project_access_pkey'),
        ForeignKeyConstraint(
            ['user_id'], ['users.skystream_users.id'],
            name='user_project_access_user_id_fkey',
        ),
        ForeignKeyConstraint(
            ['project_id'], ['users.skystream_projects.id'],
            name='user_project_access_project_id_fkey',
        ),
        {'schema': 'users'}
    )

    user_id = mapped_column(BigInteger, primary_key=True)
    project_id = mapped_column(BigInteger, primary_key=True)
    can_login = mapped_column(Boolean, nullable=False, server_default=text('true'))
    can_admin = mapped_column(Boolean, nullable=False, server_default=text('false'))
    granted_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    granted_by = mapped_column(BigInteger)
    expires_at = mapped_column(DateTime(True))


class CheckJurBalance(Base):
    __tablename__ = 'check_jur_balance'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90286_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    id_user = mapped_column(BigInteger)


class FaqTopics(Base):
    __tablename__ = 'faq_topics'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='faq_topics_pkey'),
        Index('idx_faq_topics_position', 'position'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    title = mapped_column(Text, nullable=False)
    position = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_active = mapped_column(Boolean, nullable=False,
                              server_default=text('true'))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    category = mapped_column(String)
    hot_words = mapped_column(
        ARRAY(Text()), server_default=text("'{}'::text[]"))
    popular = mapped_column(Boolean, server_default=text('false'))

    faq_answers: Mapped[List['FaqAnswers']] = relationship(
        'FaqAnswers', uselist=True, back_populates='topic')


class LkAuth(Base):
    __tablename__ = 'lk_auth'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90423456_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(BigInteger)
    date = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    ip = mapped_column(String(256))
    station_id = mapped_column(BigInteger)


class LkAuthWrong(Base):
    __tablename__ = 'lk_auth_wrong'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90426_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    date = mapped_column(DateTime(True))
    login = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    password = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    ip = mapped_column(String(255), server_default=text(
        'NULL::character varying'))
    station_id = mapped_column(BigInteger)


class LkLog(Base):
    __tablename__ = 'lk_log'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90436_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger)
    action = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    date = mapped_column(DateTime(True))
    ip = mapped_column(String)


class LkPwdChange(Base):
    __tablename__ = 'lk_pwd_change'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90442_primary'),
        Index('idx_90442_lk_pwd_change_id_uindex', 'id', unique=True),
        {'comment': 'TIME IN UTC+0 TZ', 'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    old_pwd = mapped_column(String(32), nullable=False)
    new_pwd = mapped_column(String(32), nullable=False)
    date = mapped_column(DateTime(True), nullable=False)
    ip = mapped_column(String(128), server_default=text(
        'NULL::character varying'))
    who = mapped_column(String(128))


class NetflowUsers(Base):
    __tablename__ = 'netflow_users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_netflow_users'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(Integer, nullable=False)
    flow_name = mapped_column(String, server_default=text('0'))
    network = mapped_column(CIDR, comment='Пул адресов абонента')


class Operations(Base):
    __tablename__ = 'operations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90708_primary'),
        Index('idx_90708_id_type', 'id_type'),
        Index('operations_comment_idx', 'comment'),
        Index('operations_id_type_idx', 'id_type'),
        Index('operations_id_user_from_idx', 'id_user_from'),
        Index('operations_id_user_to_idx', 'id_user_to'),
        Index('operations_uid_idx', 'uid'),
        {'comment': 'PM', 'schema': 'users'}
    )

    id = mapped_column(BigInteger, Sequence('payment_id_seq', schema='users'))
    id_user_from = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    id_user_to = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    id_type = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    comment = mapped_column(
        String(250), server_default=text('NULL::character varying'))
    amount = mapped_column(
        Double(53), server_default=text("'0'::double precision"))
    balance_before = mapped_column(
        Double(53), server_default=text("'0'::double precision"))
    balance_after = mapped_column(
        Double(53), server_default=text("'0'::double precision"))
    date = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    id_grp = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    service_len = mapped_column(Integer)
    card_number = mapped_column(
        String(30), server_default=text("'0'::character varying"))
    id_osmp = mapped_column(BigInteger)
    osmp_date = mapped_column(BigInteger)
    bill = mapped_column(BigInteger)
    data = mapped_column(Text)
    prc = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    dt = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    uid = mapped_column(Integer)


class OperationsType(Base):
    __tablename__ = 'operations_type'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90727_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger, Sequence(
        'payment_type_id_seq', schema='users'))
    for_client = mapped_column(
        SmallInteger, nullable=False, server_default=text("'1'::smallint"))
    show_admin = mapped_column(
        SmallInteger, nullable=False, server_default=text("'1'::smallint"))
    is_payment = mapped_column(
        Boolean, nullable=False, server_default=text('true'))
    name = mapped_column(
        String(50), server_default=text('NULL::character varying'))
    descr = mapped_column(
        String(255), server_default=text('NULL::character varying'))


class PrivilegedUsers(Base):
    __tablename__ = 'privileged_users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='privileged_users_pkey'),
        {'comment': 'Некоторые пользователи работают по постоплате, а некоторых не '
         'надо блокировать 1го числа, если у них отрицательный баланс. ID '
         'пользователей указаны в данной таблице.',
         'schema': 'users'}
    )

    id = mapped_column(Integer)
    comment = mapped_column(String, nullable=False)
    uid = mapped_column(Integer)
    date_create = mapped_column(Date, server_default=text('CURRENT_DATE'))
    date_end = mapped_column(Date)
    active = mapped_column(Boolean, server_default=text('true'))


class TicketCategory(Base):
    """Категории тикетов (users.ticket_categories): SLA, линия, сложность."""
    __tablename__ = 'ticket_categories'
    __table_args__ = (
        CheckConstraint("complexity IN ('L1', 'L2')", name='chk_complexity'),
        CheckConstraint(text('support_line = ANY (ARRAY[1, 2])'), name='chk_support_line'),
        PrimaryKeyConstraint('id', name='ticket_categories_pkey'),
        UniqueConstraint('slug', name='ticket_categories_slug_key'),
        ForeignKeyConstraint(['parent_id'], ['users.ticket_categories.id'], ondelete='SET NULL', name='ticket_categories_parent_id_fkey'),
        Index('idx_ticket_categories_active', 'is_active', postgresql_where=text('is_active = true')),
        Index('idx_ticket_categories_parent', 'parent_id'),
        Index('idx_ticket_categories_slug', 'slug'),
        Index('idx_ticket_categories_theme', 'theme'),
        {'schema': 'users'}
    )
    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    parent_id = mapped_column(BigInteger, nullable=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(50), nullable=False)
    theme = mapped_column(
        Enum('finance', 'network', 'equipment', 'traffic', 'other', name='tracker_theme', schema='users', create_type=False),
        nullable=False
    )
    complexity = mapped_column(String(10), nullable=False, server_default=text("'L1'"))
    priority = mapped_column(
        Enum('low', 'middle', 'high', 'critical', name='tracker_priority', schema='users', create_type=False),
        nullable=False,
        server_default=text("'middle'::users.tracker_priority")
    )
    support_line = mapped_column(SmallInteger, nullable=False, server_default=text('1'))
    sla_minutes = mapped_column(Integer, nullable=False, server_default=text('60'))
    is_active = mapped_column(Boolean, nullable=False, server_default=text('true'))
    sort_order = mapped_column(Integer, nullable=False, server_default=text('0'))
    source = mapped_column(String(10), nullable=False, server_default=text("'lk'"))
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)


class TrackerTickets(Base):
    __tablename__ = 'tracker_tickets'
    __table_args__ = (
        CheckConstraint('length(title) > 0', name='tracker_title_check'),
        CheckConstraint(
            'support_line = ANY (ARRAY[1, 2])', name='tracker_support_line_check'),
        CheckConstraint(
            "object_type IN ('user', 'station', 'other')", name='tracker_tickets_object_type_check'),
        PrimaryKeyConstraint('id', name='tracker_pkey'),
        Index('idx_tracker_author', 'author'),
        Index('idx_tracker_date_of_close', 'date_of_close'),
        Index('idx_tracker_date_of_create', 'date_of_create'),
        Index('idx_tracker_status', 'status'),
        Index('idx_tracker_subscriber_id', 'user_id'),
        Index('idx_tracker_support_line', 'support_line'),
        Index('idx_tracker_category', 'category_id'),
        Index('idx_tracker_sla_deadline', 'sla_deadline'),
        {'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=False), primary_key=True)
    author: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    support_line: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            'pending', 'open', 'in_progress',
            'waiting_client', 'waiting_technician', 'waiting_parts', 'no_technician', 'waiting_logistics', 'cc_handover',
            'waiting_cs',
            'resolved', 'closed', 'cancelled', 'deferred', 'not_resolved',
            name='tracker_status',
            schema='users',
            create_type=False
        ),
        nullable=False,
        server_default=text("'pending'::users.tracker_status")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_create: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    priority: Mapped[Optional[str]] = mapped_column(
        Enum(
            'low', 'middle', 'high', 'critical',
            name='tracker_priority',
            schema='users',
            create_type=False
        ),
        nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_of_close: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    mail_associations: Mapped[list['TrackerTicketMailLinks']] = relationship(
        'TrackerTicketMailLinks',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )
    tracker_ticket_line_history: Mapped[list['TrackerTicketLineHistory']] = relationship(
        'TrackerTicketLineHistory',
        back_populates='ticket'
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    station_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    hotspot_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    vno: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sla_deadline: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_paused_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_pause_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, server_default=text("'call_center'"))
    complexity: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, server_default=text("'L1'"))
    person_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, server_default=text('user::character varying'))
    caller_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    object_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'user'"))
    first_response_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_client_message_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Property для удобного доступа к связанным письмам
    @property
    def user_mails(self) -> list['UserMail']:
        """Получить список связанных писем"""
        return [assoc.user_mail for assoc in self.mail_associations]

    # Методы для работы со связями
    def add_user_mail(self, user_mail: 'UserMail') -> None:
        """Добавить связь с письмом"""
        if not any(assoc.user_mail_id == user_mail.id for assoc in self.mail_associations):
            association = TrackerTicketMailLinks(
                ticket_id=self.id,
                user_mail_id=user_mail.id
            )
            self.mail_associations.append(association)

    def remove_user_mail(self, user_mail: 'UserMail') -> None:
        """Удалить связь с письмом"""
        self.mail_associations = [
            assoc for assoc in self.mail_associations
            if assoc.user_mail_id != user_mail.id
        ]


class User(Base):
    __tablename__ = 'user'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90958_primary'),
        Index('idx_90958_email', 'email'),
        Index('idx_90958_full_name', 'full_name'),
        Index('idx_90958_id_grp', 'id_grp'),
        Index('idx_90958_login', 'login'),
        Index('idx_90958_password', 'password'),
        Index('idx_90958_prc_blnc', 'prc_blnc'),
        Index('idx_user_email', 'email'),
        Index('idx_user_full_name_lower'),
        Index('idx_user_login_lower'),
        Index('idx_user_juridical_id', 'juridical_id'),
        Index('idx_user_mob_tel', 'mob_tel'),
        Index('idx_users_lower_login'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    balanse = mapped_column(Double(53), nullable=False,
                            server_default=text("'0'::double precision"))
    balanse_bonus = mapped_column(
        Double(53), nullable=False, server_default=text("'0'::double precision"))
    prc_blnc = mapped_column(BigInteger, nullable=False,
                             server_default=text("'0'::bigint"))
    ppp = mapped_column(SmallInteger, nullable=False,
                        server_default=text("'0'::smallint"))
    auto_renew_stage = mapped_column(
        BigInteger, nullable=False, server_default=text("'0'::bigint"))
    last_traffic_notify = mapped_column(
        BigInteger, nullable=False, server_default=text("'0'::bigint"))
    email_agree = mapped_column(
        Boolean, nullable=False, server_default=text('true'))
    email_approve = mapped_column(
        SmallInteger, nullable=False, server_default=text("'0'::smallint"))
    login = mapped_column(
        String(255), server_default=text("''::character varying"))
    password = mapped_column(
        String(255), server_default=text("''::character varying"))
    password_service = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    id_grp = mapped_column(BigInteger)
    create_date = mapped_column(BigInteger)
    last_change_date = mapped_column(BigInteger)
    who_create = mapped_column(BigInteger)
    who_change = mapped_column(BigInteger)
    is_juridical = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    full_name = mapped_column(
        String(512), server_default=text('NULL::character varying'))
    juridical_address = mapped_column(Text)
    act_address = mapped_column(Text)
    work_tel = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    home_tel = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    mob_tel = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    web_page = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    icq_number = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    tax_number = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    email = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    passport = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    comments = mapped_column(Text)
    connect_date = mapped_column(BigInteger)
    pay_num = mapped_column(BigInteger)
    new_usr_tarif = mapped_column(Text)
    rek = mapped_column(Text)
    now_day_traffic = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    now_day_traffic_lastdate = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    now_day_traffic_lastdate_dt = mapped_column(DateTime(True))
    sms_accept_code = mapped_column(
        String(30), server_default=text('NULL::character varying'))
    sms_accepted = mapped_column(
        SmallInteger, server_default=text("'0'::smallint"))
    our_comment = mapped_column(Text)
    debug = mapped_column(Text)
    auto_renew = mapped_column(BigInteger, server_default=text("'0'::bigint"))
    remember_token = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    email_verified_at = mapped_column(DateTime(True))
    user_status = mapped_column(BigInteger)
    jur_type = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    deactivated = mapped_column(Boolean)
    jur_id = mapped_column(
        String(10), server_default=text('NULL::character varying'))
    juridical_id = mapped_column(BigInteger)
    traffic_update_hour = mapped_column(
        Integer, comment='Для безлимитных тарифов час сброса трафика по Москве')
    test_user = mapped_column(Integer, server_default=text('0'))
    hashed_password = mapped_column(String(255))
    archive = mapped_column(Integer, server_default=text(
        '0'), comment='1 - УЗ деактивирована. 0 - УЗ активна')

    temporary_sessions: Mapped[List['TemporarySessions']] = relationship(
        'TemporarySessions', uselist=True, back_populates='user')
    user_freeze_tariff: Mapped[List['UserFreezeTariff']] = relationship(
        'UserFreezeTariff', uselist=True, back_populates='user')
    reset_traffic_actions: Mapped[List['ResetTrafficAction']] = relationship(
        'ResetTrafficAction',
        back_populates='user',
        cascade='all, delete-orphan'
    )


class UserArchive(Base):
    __tablename__ = 'user_archive'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91002_primary'),
        {'comment': 'Архивные пользователи', 'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    user_login = mapped_column(String(255), nullable=False)
    user_data = mapped_column(Text, nullable=False)


class UserComments(Base):
    __tablename__ = 'user_comments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91018_primary'),
        Index('user_comments_id_author_idx', 'id_author'),
        Index('user_comments_id_user_idx', 'id_user'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    id_user = mapped_column(BigInteger, nullable=False,
                            server_default=text("'0'::bigint"))
    datum = mapped_column(DateTime(True))
    data = mapped_column(Text)
    id_author = mapped_column(BigInteger, server_default=text("'0'::bigint"))


class UserDetails(Base):
    __tablename__ = 'user_details'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91027_primary'),
        Index('idx_91027_user_details_fk', 'user_id'),
        Index('idx_user_details_name_lower'),
        Index('idx_user_details_patronymic_lower'),
        Index('idx_user_details_surname_lower'),
        {'comment': 'Паспортные данные пользователей', 'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    pas_series = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    pas_number = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    pas_date = mapped_column(Date)
    pas_code = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    surname = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    name = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    patronymic = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    date_birth = mapped_column(Date)
    address = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    country = mapped_column(
        String(10), server_default=text("'ru'::character varying"))
    is_actual = mapped_column(Boolean, server_default=text('true'))
    region = mapped_column(
        String(128), server_default=text('NULL::character varying'))
    city = mapped_column(
        String(64), server_default=text('NULL::character varying'))
    street = mapped_column(
        String(128), server_default=text('NULL::character varying'))
    house = mapped_column(
        String(64), server_default=text('NULL::character varying'))
    flat = mapped_column(
        String(64), server_default=text('NULL::character varying'))


class UserDetailsHistoryOfChange(Base):
    __tablename__ = 'user_details_history_of_change'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9107777_primary'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    pas_series = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    pas_number = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    pas_date = mapped_column(Date)
    pas_code = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    surname = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    name = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    patronymic = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    date_birth = mapped_column(Date)
    address = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    date_of_change = mapped_column(DateTime)


class UserEmailApprove(Base):
    __tablename__ = 'user_email_approve'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91041_primary'),
        Index('idx_91041_user_email_approve_id_uindex', 'id', unique=True),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger)
    email = mapped_column(
        String(128), server_default=text('NULL::character varying'))
    key_value = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    date = mapped_column(
        DateTime(True), server_default=text('CURRENT_TIMESTAMP'))


class UserEmailSend(Base):
    __tablename__ = 'user_email_send'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91049_primary'),
        Index('idx_91049_user_email_send_id_uindex', 'id', unique=True),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    login = mapped_column(String(128), nullable=False)
    type = mapped_column(String(32), nullable=False)
    date = mapped_column(DateTime(True), nullable=False)


class UserMail(Base):
    __tablename__ = 'user_mail'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_95218_primary'),
        Index('idx_95218_uniq_date', 'id_user_from',
              'id_user_to', 'date', unique=True),
        Index('user_mail_answer_idx', 'answer'),
        Index('user_mail_id_user_from_idx', 'id_user_from'),
        Index('user_mail_id_user_to_idx', 'id_user_to'),
        {'comment': 'Сообщения поддержки', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=False), primary_key=True)
    view_from: Mapped[str] = mapped_column(Enum(
        '0', '1', name='user_mail_view_from'), nullable=False, server_default=text("'1'::user_mail_view_from"))
    view_to: Mapped[str] = mapped_column(Enum(
        '0', '1', name='user_mail_view_to'), nullable=False, server_default=text("'1'::user_mail_view_to"))
    answer: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text('0'))
    file: Mapped[str] = mapped_column(
        String(256), nullable=False, server_default=text("''::character varying"))
    id_user_from: Mapped[int] = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    id_user_to: Mapped[int] = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    date: Mapped[int] = mapped_column(
        BigInteger, server_default=text("'0'::bigint"))
    read: Mapped[str] = mapped_column(Enum(
        '0', '1', name='user_mail_read'), server_default=text("'0'::user_mail_read"))
    text_: Mapped[str] = mapped_column('text', Text)
    new: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    cs_answer: Mapped[str] = mapped_column(Enum(
        '1', '0', name='user_mail_cs_answer'), server_default=text("'0'::user_mail_cs_answer"))
    file_new: Mapped[str] = mapped_column(
        String(255), server_default=text("'0'::character varying"))
    Дата: Mapped[DateTime] = mapped_column(DateTime(True))
    ip_address: Mapped[str] = mapped_column(INET)
    real_file = mapped_column(Text)
    date_tz: Mapped[DateTime] = mapped_column(
        DateTime(True), server_default=text('now()'))
    relay_msg_id: Mapped[str] = mapped_column(String, nullable=True)
    person_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_chat: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ticket_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True), nullable=True)
    # Relationships
    ticket_associations: Mapped[list['TrackerTicketMailLinks']] = relationship(
        'TrackerTicketMailLinks',
        back_populates='user_mail',
        cascade='all, delete-orphan'
    )

    # Property для удобного доступа к связанным тикетам
    @property
    def tickets(self) -> list['TrackerTickets']:
        """Получить список связанных тикетов"""
        return [assoc.ticket for assoc in self.ticket_associations]


class UserMailAttachment(Base):
    """Вложения к сообщениям чата (файлы по msg_id)."""
    __tablename__ = 'user_mail_attachments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_mail_attachments_pkey'),
        Index('idx_user_mail_attachments_msg_id', 'msg_id'),
        {'comment': 'Вложения сообщений чата', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    msg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_mail.id', ondelete='CASCADE'), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False, server_default=text("''"))
    file_ext: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class TrackerMessageAttachment(Base):
    """Вложения к сообщениям трекера (tracker_messages для KS/partner/tech)."""
    __tablename__ = 'tracker_message_attachments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tracker_message_attachments_pkey'),
        Index('idx_tracker_msg_attach_msg_id', 'msg_id'),
        {'comment': 'Вложения сообщений трекера', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    msg_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.tracker_messages.id', ondelete='CASCADE'),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(
        String(512), nullable=False, server_default=text("''"))
    file_ext: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class UserMailReads(Base):
    __tablename__ = 'user_mail_reads'
    __table_args__ = (
        UniqueConstraint('msg_id', 'user_id', 'person_type', 
                        name='idx_user_mail_reads_unique'),
        Index('idx_user_mail_reads_msg_id', 'msg_id'),
        Index('idx_user_mail_reads_user_id', 'user_id'),
        Index('idx_user_mail_reads_read_time', 'read_time'),
        {'comment': 'Прочтения сообщений', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(
        BigInteger, 
        Identity(always=False), 
        primary_key=True
    )
    msg_id: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False,
        comment='ID сообщения'
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False,
        comment='ID пользователя'
    )
    person_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='Тип участника (from/to)'
    )
    read_time: Mapped[datetime] = mapped_column(
        DateTime(True),  # True = timezone=True (timestamptz)
        nullable=False, 
        server_default=text('now()'),
        comment='Время прочтения'
    )

class UserServiceDate(Base):
    __tablename__ = 'user_service_date'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91084_primary'),
        Index('idx_91084_user_service_date_user_id_uindex',
              'user_id', unique=True),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    username = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    service = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    on_date = mapped_column(DateTime(True))
    valid_date = mapped_column(DateTime(True))
    len = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger)
    traffic_renew_count = mapped_column(
        Integer,
        nullable=True,
        comment='Остаток доступных сбросов трафика (безлимитные ФЛ)',
    )


class UsersLkTokens(Base):
    __tablename__ = 'users_lk_tokens'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_abs_ref_tokens_pkey'),
        Index('users_lk_tokens_user_id_idx', 'user_id'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(Integer, nullable=False)
    token = mapped_column(String(255), nullable=False)
    create_date = mapped_column(
        DateTime, server_default=text('CURRENT_TIMESTAMP'))
    canceled_date = mapped_column(DateTime, server_default=text(
        "(CURRENT_TIMESTAMP + '30 days'::interval)"))
    ip_address = mapped_column(String(45))



class AbsLoginHistory(Base):
    __tablename__ = 'abs_login_history'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.skystream_users.id'],
                             ondelete='RESTRICT', name='abs_login_history_user_id_fkey'),
        ForeignKeyConstraint(
            ['user_id'], ['users.skystream_users.id'], name='fk_login_history_user'),
        PrimaryKeyConstraint('id', name='abs_login_history_pkey'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    login_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    success = mapped_column(Boolean, nullable=False)
    ip_address = mapped_column(INET)
    failure_reason = mapped_column(Text)


class AbsUserTokens(Base):
    __tablename__ = 'abs_user_tokens'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.skystream_users.id'],
                             ondelete='CASCADE', name='abs_user_tokens_user_id_fkey'),
        PrimaryKeyConstraint('id', name='abs_user_tokens_pkey'),
        UniqueConstraint('refresh_jti', 'is_revoked',
                         name='unique_active_refresh'),
        UniqueConstraint(
            'refresh_jti', name='abs_user_tokens_refresh_jti_key'),
        Index('ix_abs_user_tokens_cleanup', 'refresh_expires_at'),
        Index('ix_abs_user_tokens_refresh_jti', 'refresh_jti'),
        Index('ix_abs_user_tokens_access_jti', 'access_jti'),
        Index('ix_abs_user_tokens_user_active', 'user_id'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    access_jti = mapped_column(Uuid, nullable=False)
    refresh_jti = mapped_column(Uuid, nullable=False)
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    access_expires_at = mapped_column(DateTime(True), nullable=False)
    refresh_expires_at = mapped_column(DateTime(True), nullable=False)
    is_revoked = mapped_column(
        Boolean, nullable=False, server_default=text('false'))
    device_info = mapped_column(Text)
    ip_address = mapped_column(INET)
    user_agent = mapped_column(Text)
    revoked_at = mapped_column(DateTime(True))


class FaqAnswers(Base):
    __tablename__ = 'faq_answers'
    __table_args__ = (
        ForeignKeyConstraint(['topic_id'], ['users.faq_topics.id'],
                             ondelete='CASCADE', name='faq_answers_topic_id_fkey'),
        PrimaryKeyConstraint('id', name='faq_answers_pkey'),
        Index('idx_faq_answers_position', 'position'),
        Index('idx_faq_answers_topic_id', 'topic_id'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    topic_id = mapped_column(BigInteger, nullable=False)
    page_title = mapped_column(Text, nullable=False)
    text_ = mapped_column('text', Text, nullable=False)
    position = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    hot_words = mapped_column(
        ARRAY(Text()), server_default=text("'{}'::text[]"))
    for_copy = mapped_column(Boolean, server_default=text(
        'false'), comment='Можно ли копировать это собщение')

    topic: Mapped['FaqTopics'] = relationship(
        'FaqTopics', back_populates='faq_answers')


class TemporarySessions(Base):
    __tablename__ = 'temporary_sessions'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user.id'], ondelete='RESTRICT',
                             onupdate='RESTRICT', name='temporary_sessions_fk'),
        PrimaryKeyConstraint('id', name='idx_90925_primary'),
        Index('idx_90925_temporary_sessions_fk', 'user_id'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger)
    ip_address = mapped_column(Text)
    date_start = mapped_column(DateTime(True))

    user: Mapped[Optional['User']] = relationship(
        'User', back_populates='temporary_sessions')


class TrackerMessages(Base):
    __tablename__ = 'tracker_messages'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tracker_messages_pkey'),
        Index('idx_tracker_messages_author_id', 'author_id'),
        Index('idx_tracker_messages_chat_id', 'ticket_id'),
        Index('idx_tracker_messages_created_at', 'created_at'),
        Index('idx_tracker_messages_incident_id', 'incident_id'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger, Sequence('tracker_id_seq', schema='users'))
    # ticket_id nullable после миграции add_incident_assignments_messages.sql
    ticket_id = mapped_column(BigInteger, nullable=True)
    # incident_id заполняется для сообщений чата инцидентов (monitoring.incidents)
    incident_id = mapped_column(BigInteger, nullable=True)
    author_id = mapped_column(BigInteger, nullable=False)
    body = mapped_column(Text, nullable=False)
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    is_edited = mapped_column(Boolean, nullable=False,
                              server_default=text('false'))
    updated_at = mapped_column(DateTime(True))
    person_type = mapped_column(String(20), nullable=True,
                                comment='Тип автора: skystream | tech | partner')
    reply_to_id = mapped_column(BigInteger, nullable=True,
                                comment='ID сообщения, на которое отвечают')


class TrackerMessagesReads(Base):
    """Прочтения сообщений трекера (tracker_messages)."""
    __tablename__ = 'tracker_messages_reads'
    __table_args__ = (
        UniqueConstraint('msg_id', 'user_id', 'person_type',
                         name='idx_tracker_msg_reads_unique'),
        Index('idx_tracker_msg_reads_msg_id', 'msg_id'),
        Index('idx_tracker_msg_reads_user_id', 'user_id'),
        Index('idx_tracker_msg_reads_read_time', 'read_time'),
        {'comment': 'Прочтения сообщений трекера', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=False), primary_key=True)
    msg_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment='ID сообщения из tracker_messages')
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment='ID пользователя, который прочитал')
    person_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment='Тип участника: skystream | tech | partner')
    read_time: Mapped[datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'),
        comment='Время прочтения')


class TrackerTicketLineHistory(Base):
    __tablename__ = 'tracker_ticket_line_history'
    __table_args__ = (
        CheckConstraint(
            '(support_line IS NULL OR support_line = ANY (ARRAY[1, 2]))',
            name='tracker_ticket_line_history_support_line_check',
        ),
        ForeignKeyConstraint(['ticket_id'], ['users.tracker_tickets.id'],
                             ondelete='CASCADE', name='fk_tracker_ticket_line_history_ticket'),
        PrimaryKeyConstraint('id', name='tracker_ticket_line_history_pkey'),
        Index('idx_tracker_ticket_line_history_start_time', 'start_time'),
        Index('idx_tracker_ticket_line_history_support_line', 'support_line'),
        Index('idx_tracker_ticket_line_history_ticket_id', 'ticket_id'),
        Index('idx_tracker_ticket_line_history_event_type', 'event_type'),
        {'schema': 'users'}
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    ticket_id = mapped_column(BigInteger, nullable=False)
    support_line = mapped_column(SmallInteger, nullable=True)
    start_time = mapped_column(
        DateTime(True), nullable=False, server_default=text('now()'))
    end_time = mapped_column(DateTime(True))
    changed_by = mapped_column(BigInteger)
    event_type = mapped_column(String(50), nullable=True)
    payload = mapped_column(JSONB, nullable=True)
    # 'active' — линия работает | 'waiting_client' — ждём ответа абонента
    state = mapped_column(String(20), nullable=True, server_default=text("'active'"))

    ticket: Mapped['TrackerTickets'] = relationship(
        'TrackerTickets', back_populates='tracker_ticket_line_history')


class TrackerTicketExecutors(Base):
    """Исполнители-помощники по тикету (сопоставление ticket_id — abs_user_id)."""
    __tablename__ = 'tracker_ticket_executors'
    __table_args__ = (
        ForeignKeyConstraint(['ticket_id'], ['users.tracker_tickets.id'],
                             ondelete='CASCADE', name='fk_tracker_ticket_executors_ticket'),
        ForeignKeyConstraint(['abs_user_id'], ['users.skystream_users.id'],
                             ondelete='CASCADE', name='fk_tracker_ticket_executors_abs_user'),
        PrimaryKeyConstraint('ticket_id', 'abs_user_id', name='tracker_ticket_executors_pkey'),
        Index('idx_tracker_ticket_executors_ticket_id', 'ticket_id'),
        Index('idx_tracker_ticket_executors_abs_user_id', 'abs_user_id'),
        {'schema': 'users'}
    )

    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    abs_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text('now()')
    )


class TrackerTicketTechnicians(Base):
    """Техники партнёра, добавленные к тикету (technician_id из partner.technicians)."""
    __tablename__ = 'tracker_ticket_technicians'
    __table_args__ = (
        ForeignKeyConstraint(['ticket_id'], ['users.tracker_tickets.id'],
                             ondelete='CASCADE', name='fk_tracker_ticket_technicians_ticket'),
        PrimaryKeyConstraint('ticket_id', 'technician_id', name='tracker_ticket_technicians_pkey'),
        Index('idx_tracker_ticket_technicians_ticket_id', 'ticket_id'),
        Index('idx_tracker_ticket_technicians_technician_id', 'technician_id'),
        {'schema': 'users'}
    )

    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    technician_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text('now()')
    )


class TrackerSlaConfig(Base):
    """Правила SLA по линиям техподдержки. Редактируется вручную в БД."""
    __tablename__ = 'tracker_sla_config'
    __table_args__ = (
        UniqueConstraint('support_line', 'priority', name='uq_sla_line_priority'),
        {'schema': 'users'},
    )

    id:                   Mapped[int]           = mapped_column(Integer, primary_key=True)
    support_line:         Mapped[int]           = mapped_column(SmallInteger, nullable=False)
    priority:             Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    name:                 Mapped[str]           = mapped_column(String(100), nullable=False)

    # Время первого ответа (минуты)
    response_min_work:    Mapped[int]           = mapped_column(SmallInteger, nullable=False)
    response_min_nonwork: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    # Рабочий период
    work_start_hour:      Mapped[int]           = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    work_end_hour:        Mapped[int]           = mapped_column(SmallInteger, nullable=False, server_default=text('24'))
    work_days:            Mapped[str]           = mapped_column(String(20), nullable=False, server_default=text("'1,2,3,4,5,6,7'"))

    # Время решения (часы; NULL = не контролируется)
    resolution_hours_work: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    is_active:            Mapped[bool]          = mapped_column(Boolean, nullable=False, server_default=text('TRUE'))
    notes:                Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:           Mapped[DateTime]      = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at:           Mapped[DateTime]      = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'))


class TrackerTicketMailLinks(Base):
    __tablename__ = 'tracker_ticket_mail_links'
    __table_args__ = (
        ForeignKeyConstraint(['ticket_id'], ['users.tracker_tickets.id'],
                             ondelete='CASCADE',
                             name='fk_tracker_ticket_mail_links_ticket'),
        ForeignKeyConstraint(['user_mail_id'], ['users.user_mail.id'],
                             ondelete='CASCADE',
                             name='fk_tracker_ticket_mail_links_mail'),
        PrimaryKeyConstraint('ticket_id', 'user_mail_id',
                             name='tracker_ticket_mail_links_pkey'),
        Index('idx_tracker_ticket_mail_links_ticket_id', 'ticket_id'),
        Index('idx_tracker_ticket_mail_links_user_mail_id', 'user_mail_id'),
        {'schema': 'users'}
    )

    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_mail_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Relationships
    ticket: Mapped['TrackerTickets'] = relationship(
        'TrackerTickets',
        back_populates='mail_associations'
    )
    user_mail: Mapped['UserMail'] = relationship(
        'UserMail',
        back_populates='ticket_associations'
    )


class UserFreezeReasonCode(Base):
    __tablename__ = 'user_freeze_reason_codes'
    __table_args__ = ({'schema': 'users'},)
    id = mapped_column(Integer, primary_key=True)
    short_reason = mapped_column(String(128), nullable=False)
    rus_reason = mapped_column(String(128), nullable=True)
    description = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at = mapped_column(DateTime(True), server_default=text('now()'), onupdate=text('now()'))


class UserFreezeTariff(Base):
    __tablename__ = 'user_freeze_tariff'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user.id'], ondelete='RESTRICT',
                             onupdate='RESTRICT', name='user_freeze_tariff_user_fk'),
        ForeignKeyConstraint(['reason_code'], ['users.user_freeze_reason_codes.id'], ondelete='SET NULL',
                             onupdate='RESTRICT', name='user_freeze_tariff_reason_fk'),
        PrimaryKeyConstraint('id', name='idx_91054_primary'),
        Index('idx_91054_user_freeze_tariff_unique', 'user_id', unique=True),
        {'comment': 'Замороженные тарифы', 'schema': 'users'}
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    user_id = mapped_column(BigInteger, nullable=False, comment='Пользователь')
    tariff = mapped_column(String(128), nullable=True, comment='sname тарифа (NULL = запланированная заморозка)')
    unlimited = mapped_column(Boolean, nullable=True,
                              comment='1 - Безлимитный, 0 - Лимитный')
    remaining_traffic = mapped_column(
        BigInteger, nullable=True, comment='Оставшийся трафик в байтах')
    remaining_time = mapped_column(
        BigInteger, nullable=True, comment='Оставшееся время в секундах')
    date_freeze = mapped_column(DateTime(True), nullable=False, server_default=text(
        'CURRENT_TIMESTAMP'), comment='Дата начала заморозки (расписание)')
    create_date = mapped_column(DateTime(True), nullable=True, server_default=text('now()'),
                                comment='Дата создания записи в БД')
    full_packet = mapped_column(BigInteger)
    total_days = mapped_column(Integer)
    reason = mapped_column(String(256))
    reason_code = mapped_column(Integer, nullable=True, comment='FK users.user_freeze_reason_codes')
    date_unfreeze = mapped_column(DateTime(True))
    is_frozen = mapped_column(Boolean, nullable=False, server_default=text('false'),
                              comment='True — заморозка исполнена, False — только расписание на будущее')

    user: Mapped['User'] = relationship(
        'User', back_populates='user_freeze_tariff')


#########################
### DATABASE HELPDESK ###
#########################


class DBCategory(Base):
    __tablename__ = 'db_categories'
    __table_args__ = (
        {'comment': 'Категории базы знаний', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment='Название категории')

    # Внешний ключ на саму себя
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey('users.db_categories.id', ondelete='SET NULL'),
        nullable=True,
        comment='ID родительской категории'
    )

    icon: Mapped[str] = mapped_column(
        String(50), server_default='📁', comment='Иконка или эмодзи')
    color: Mapped[str] = mapped_column(
        String(50), server_default='#3b82f6', comment='Цвет категории')
    order: Mapped[int] = mapped_column(
        Integer, server_default=text('0'), comment='Порядок сортировки')

    # ИСПРАВЛЕННЫЕ ОТНОШЕНИЯ
    # 1. Дети: Отношение к потомкам (без remote_side)
    children: Mapped[List['DBCategory']] = relationship(
        'DBCategory',
        back_populates='parent',
        cascade='all, delete-orphan'
    )

    # 2. Родитель: Отношение к предку (ЗДЕСЬ нужен remote_side=[id])
    parent: Mapped[Optional['DBCategory']] = relationship(
        'DBCategory',
        remote_side=[id],
        back_populates='children'
    )

    # Связь со статьями
    articles: Mapped[List['DBArticle']] = relationship(
        'DBArticle', back_populates='category')


class DBArticle(Base):
    __tablename__ = 'db_articles'
    __table_args__ = (
        {'comment': 'Статьи (вопросы) базы знаний', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.db_categories.id', ondelete='CASCADE'),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment='Заголовок статьи')
    is_popular: Mapped[bool] = mapped_column(Boolean, server_default=text(
        'false'), nullable=False, comment='Популярный вопрос')
    view_count: Mapped[int] = mapped_column(Integer, server_default=text(
        '0'), nullable=False, comment='Количество просмотров')
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    # Отношения
    category: Mapped['DBCategory'] = relationship(
        'DBCategory', back_populates='articles')
    nodes: Mapped[List['DBNode']] = relationship(
        'DBNode', back_populates='article', cascade='all, delete-orphan')


class DBNode(Base):
    __tablename__ = 'db_nodes'
    __table_args__ = (
        {'comment': 'Узлы дерева решений', 'schema': 'users'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.db_articles.id', ondelete='CASCADE'),
        nullable=False
    )

    # Внешний ключ на самого себя
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey('users.db_nodes.id', ondelete='CASCADE'),
        nullable=True,
        comment='Родительский узел'
    )

    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment='Текст ответа/инструкции')
    option_label: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment='Текст на кнопке выбора')
    is_final: Mapped[bool] = mapped_column(Boolean, server_default=text(
        'false'), nullable=False, comment='Финальный ответ')

    # Отношения со статьей
    article: Mapped['DBArticle'] = relationship(
        'DBArticle', back_populates='nodes')
    script: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment='Текст для копирования клиенту')
    # ИСПРАВЛЕННЫЕ ОТНОШЕНИЯ (Аналогично категориям)
    # 1. Дети (следующие шаги)
    children: Mapped[List['DBNode']] = relationship(
        'DBNode',
        back_populates='parent',
        cascade='all, delete-orphan'
    )

    # 2. Родитель (предыдущий шаг) - remote_side=[id] указывает, что parent_id ссылается на id
    parent: Mapped[Optional['DBNode']] = relationship(
        'DBNode',
        remote_side=[id],
        back_populates='children'
    )


class RemoveFromDistribution(Base):
    __tablename__ = 'remove_from_distribution'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', name='remove_from_distribution_pkey'),
        {'comment': 'В этой таблице хранятся пользователи, которых временно или никогда нельзя проверять скриптом распределения по IP группам.', 'schema': 'users'}
    )

    # Привязка к основной таблице пользователей с каскадным удалением
    user_id = mapped_column(
        BigInteger,
        ForeignKey('users.user.id', ondelete='CASCADE'),
        nullable=False
    )
    # 1 - на 7 дней, 2 - навсегда
    status = mapped_column(SmallInteger, nullable=False)
    # Дата истечения (в Postgres это будет TIMESTAMPTZ)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)
    # Дата создания записи
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class OperatorFavorite(Base):
    __tablename__ = 'operator_favorites'
    __table_args__ = (
        PrimaryKeyConstraint('operator_id', 'subscriber_id',
                             name='operator_favorites_pkey'),
        {'comment': 'Персональные списки избранных абонентов для каждого инженера',
            'schema': 'users'}
    )

    # ID инженера (ссылка на системного пользователя)
    operator_id = mapped_column(
        BigInteger,
        ForeignKey('users.skystream_users.id', ondelete='CASCADE'),
        nullable=False
    )

    # ID абонента (ссылка на таблицу абонентов)
    subscriber_id = mapped_column(
        BigInteger,
        ForeignKey('users.user.id', ondelete='CASCADE'),
        nullable=False
    )

    # Дата добавления в избранное
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class ResetTrafficAction(Base):
    __tablename__ = 'reset_traffic_actions'
    __table_args__ = {'schema': 'users'}

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment='Первичный ключ')
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        'users.user.id', ondelete='CASCADE'), nullable=False, comment='ID пользователя')
    timestamp: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), default=func.now(), nullable=False, comment='Дата и время сброса')
    who: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment='Кто выполнил сброс')
    author_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey(
        'users.skystream_users.id', ondelete='SET NULL'), nullable=True)

    # Relationships (опционально)
    user = relationship('User', back_populates='reset_traffic_actions')
    author = relationship('SkystreamUsers', back_populates='authored_reset_actions')


class WhiteIpAddress(Base):
    """Белые IP-адреса абонентов. FK создаются миграцией (cross-schema)."""
    __tablename__ = 'white_ip_addresses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='white_ip_addresses_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.user.id'],
                             name='fk_user', ondelete='CASCADE'),
        CheckConstraint(
            'date_stop IS NULL OR date_stop > date_start', name='valid_dates'),
        {'schema': 'users'}
    )

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(BigInteger, nullable=False)
    station_id = mapped_column(BigInteger, nullable=False)
    ip_address = mapped_column(INET, nullable=False)
    date_start = mapped_column(
        DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    date_stop = mapped_column(DateTime(True))
    created_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = mapped_column(
        DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))


class UserRegistrations(Base):
    """Регистрация абонента (users.user_registrations)."""

    __tablename__ = "user_registrations"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="user_registrations_pkey"),
        {"schema": "users"},
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    registration_date = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    last_name = mapped_column(String(100), nullable=False)
    first_name = mapped_column(String(100), nullable=False)
    middle_name = mapped_column(String(100), nullable=True)
    station_id = mapped_column(Integer, nullable=False)
    hotspot_id = mapped_column(Integer, nullable=False)
    vno_id = mapped_column(Integer, nullable=False)
    user_id = mapped_column(Integer, nullable=False)
    source = mapped_column(String, nullable=False, server_default=text("'lk'::character varying"))
    registered_by = mapped_column(Integer, nullable=True)
    person_type = mapped_column(String, nullable=True)
    pasport = mapped_column(String, nullable=False)


class FastCheckDatabase(Base):
    """Справочник быстрой проверки абонента (users.fast_check_database)."""

    __tablename__ = "fast_check_database"
    __table_args__ = (
        UniqueConstraint("test_code", "variant", name="fast_check_database_test_variant_uq"),
        CheckConstraint("priority > 0", name="fast_check_database_priority_positive"),
        Index("ix_fast_check_database_priority_active", "priority"),
        Index("ix_fast_check_database_test_code", "test_code"),
        {
            "schema": "users",
            "comment": "Шаги быстрой проверки: код теста, подпись, HTML-инструкция при сбое",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    test_code: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Код проверки в приложении"
    )
    variant: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Уточнение: 0 — по умолчанию; иначе числовой подтип сбоя",
    )
    check_label: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="Подпись шага в списке проверок"
    )
    actions_html: Mapped[str] = mapped_column(
        Text, nullable=False, comment="HTML: действия оператора при сбое"
    )
    priority: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="Порядок выполнения (меньше — раньше)"
    )
    stop_on_fail: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), comment="Остановить цепочку при сбое"
    )
    match_flags: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Доп. условия сопоставления (резерв)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("NOW()")
    )


class PasswordResetCode(Base):
    __tablename__ = "password_reset_code"
    __table_args__ = {"schema": "users"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.user.id', ondelete="CASCADE"), nullable=False
    )
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.skystream_users.id", ondelete="RESTRICT"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code_salt: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    used_ip: Mapped[Optional[str]] = mapped_column(INET)
    deactivation_reason: Mapped[Optional[str]] = mapped_column(String(32))
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
