from datetime import datetime
from typing import List

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Articles(Base):
    __tablename__ = 'articles'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='articles_pkey'),
        UniqueConstraint('slug', name='articles_slug_key'),
        Index('idx_articles_category', 'category'),
        Index('idx_articles_created_at', 'created_at'),
        Index('idx_articles_slug', 'slug'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    slug = mapped_column(String(255), nullable=False)
    title = mapped_column(String(255), nullable=False)
    content = mapped_column(Text, nullable=False)
    subtitle = mapped_column(String(255))
    author = mapped_column(String(255))
    category = mapped_column(String(100))
    created_at = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    reading_time = mapped_column(Integer, server_default=text('5'))
    allow_pdf = mapped_column(Boolean, server_default=text('false'))


class NoteidIdgrp(Base):
    __tablename__ = 'noteid_idgrp'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idgrp_noteid'),
        Index('idx_noteid_idgrp_note_id', 'note_id'),
        Index('idx_noteid_idgrp_id_grp', 'id_grp'),
        {'comment': 'Какая группа какую новость должна видеть',
     'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    id_grp = mapped_column(BigInteger, server_default=text('0'))
    note_id = mapped_column(BigInteger)


class NewsAttachment(Base):
    """Вложения к новостям (user_notification или partner_news)."""
    __tablename__ = 'news_attachment'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='news_attachment_pkey'),
        Index('idx_news_attachment_target', 'target_type', 'target_id'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    target_type = mapped_column(String(32), nullable=False)  # 'user_notification' | 'partner_news'
    target_id = mapped_column(BigInteger, nullable=False)
    original_filename = mapped_column(Text, nullable=False)
    stored_filename = mapped_column(Text, nullable=False)
    file_path = mapped_column(Text, nullable=False)
    mime_type = mapped_column(String(100), nullable=False)
    file_size_bytes = mapped_column(BigInteger, nullable=False)
    uploaded_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class PartnerNews(Base):
    __tablename__ = 'partner_news'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='partner_notification7_pkey'),
        Index('idx_partner_news_create_time', 'create_time'),
        Index('idx_partner_news_id_diler', 'id_diler'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    create_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    id_diler = mapped_column(BigInteger, server_default=text('0'))
    message = mapped_column(Text)
    title = mapped_column(Text)
    active = mapped_column(Integer, server_default=text('0'))
    scheduled_at = mapped_column(DateTime(True), nullable=True, comment='Отложенная публикация')
    published_at = mapped_column(DateTime(True), nullable=True, comment='Фактическое время публикации')

class ReadNotification(Base):
    __tablename__ = 'read_notification'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='read_notification_pkey'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger, primary_key=True)  # bigserial автоматически генерируется
    read_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    id_grp = mapped_column(BigInteger, server_default=text('0'))
    user_id = mapped_column(BigInteger)
    note_id = mapped_column(BigInteger)


class PartnerReadNews(Base):
    __tablename__ = 'partner_read_news'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='read_notification7_pkey'),
        Index('idx_partner_read_news_unique', 'user_id', 'note_id', unique=True),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger, primary_key=True)  # Значение по умолчанию из последовательности
    read_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    user_id = mapped_column(BigInteger)
    note_id = mapped_column(BigInteger)

class PartnerNotification(Base):
    __tablename__ = 'partner_notification'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='partner_notification_pkey'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    create_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    id_diler = mapped_column(BigInteger, server_default=text('0'), comment='0 - никому, 1 - всем. Либо ID партнера')
    message = mapped_column(Text)
    title = mapped_column(Text)
    importance = mapped_column(Integer, server_default=text('0'))
    active = mapped_column(Integer, server_default=text('0'))


class ProposalCategories(Base):
    __tablename__ = 'proposal_categories'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='proposal_categories_pkey'),
        UniqueConstraint('name', name='proposal_categories_name_key'),
        {'schema': 'notification'}
    )

    id = mapped_column(Integer)
    name = mapped_column(String(50), nullable=False)

    proposals: Mapped[List['Proposals']] = relationship('Proposals', uselist=True, back_populates='category')


class ProposalPriorities(Base):
    __tablename__ = 'proposal_priorities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='proposal_priorities_pkey'),
        UniqueConstraint('name', name='proposal_priorities_name_key'),
        UniqueConstraint('sort_order', name='proposal_priorities_sort_order_key'),
        {'schema': 'notification'}
    )

    id = mapped_column(Integer)
    name = mapped_column(String(20), nullable=False)
    sort_order = mapped_column(Integer, nullable=False)

    proposals: Mapped[List['Proposals']] = relationship('Proposals', uselist=True, back_populates='priority')


class ProposalStatuses(Base):
    __tablename__ = 'proposal_statuses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='proposal_statuses_pkey'),
        UniqueConstraint('name', name='proposal_statuses_name_key'),
        {'schema': 'notification'}
    )

    id = mapped_column(Integer)
    name = mapped_column(String(30), nullable=False)

    proposals: Mapped[List['Proposals']] = relationship('Proposals', uselist=True, back_populates='status')


class UserNotification(Base):
    __tablename__ = 'user_notification'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_notification_pkey'),
        Index('idx_user_notification_create_time', 'create_time'),
        Index('idx_user_notification_user_id', 'user_id'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    create_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    message = mapped_column(Text)
    title = mapped_column(Text)
    active = mapped_column(Integer, server_default=text('1'))
    views = mapped_column(BigInteger, server_default=text('0'))
    image_url = mapped_column(String(512))
    user_id = mapped_column(BigInteger, server_default=text("'-1'::integer"), comment='-1 - Это для всех пользователей. Любой ID пользователя')
    scheduled_at = mapped_column(DateTime(True), nullable=True, comment='Отложенная публикация')
    published_at = mapped_column(DateTime(True), nullable=True, comment='Фактическое время публикации')


class NewsPost(Base):
    """Единая новость (notification.news): партнёры и абоненты."""
    __tablename__ = "news"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="news_pkey"),
        {"schema": "notification"},
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    title = mapped_column(Text, nullable=False)
    body_html = mapped_column(Text, nullable=False, server_default=text("''"))
    summary_text = mapped_column(Text, nullable=True)
    author_user_id = mapped_column(BigInteger, nullable=True)
    author_display_name = mapped_column(Text, nullable=True)
    is_active = mapped_column(Boolean, nullable=False, server_default=text("true"))
    scheduled_publish_at = mapped_column(DateTime(True), nullable=True)
    published_at = mapped_column(DateTime(True), nullable=True)
    expires_at = mapped_column(DateTime(True), nullable=True)
    is_archived = mapped_column(Boolean, nullable=False, server_default=text("false"))
    archived_at = mapped_column(DateTime(True), nullable=True)
    scope_all_partners = mapped_column(Boolean, nullable=False, server_default=text("false"))
    scope_all_subscribers = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_important = mapped_column(Boolean, nullable=False, server_default=text("false"))
    meta = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))


class NewsFile(Base):
    """Файлы/изображения новости (notification.news_file)."""
    __tablename__ = "news_file"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="news_file_pkey"),
        UniqueConstraint("news_id", "sort_order", name="uq_news_file_order"),
        ForeignKeyConstraint(["news_id"], ["notification.news.id"], ondelete="CASCADE", name="news_file_news_id_fkey"),
        Index("idx_news_file_by_news", "news_id", "sort_order"),
        {"schema": "notification"},
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    news_id = mapped_column(BigInteger, nullable=False)
    sort_order = mapped_column(Integer, nullable=False, server_default=text("0"))
    stored_path = mapped_column(Text, nullable=False)
    original_filename = mapped_column(Text, nullable=True)
    mime_type = mapped_column(String(128), nullable=False)
    file_size_bytes = mapped_column(BigInteger, nullable=False)
    width_px = mapped_column(Integer, nullable=True)
    height_px = mapped_column(Integer, nullable=True)
    alt_text = mapped_column(Text, nullable=True)
    uploaded_at = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))


class NewsScopePartner(Base):
    __tablename__ = "news_scope_partner"
    __table_args__ = (
        PrimaryKeyConstraint("news_id", "partner_id", name="news_scope_partner_pkey"),
        ForeignKeyConstraint(["news_id"], ["notification.news.id"], ondelete="CASCADE", name="news_scope_partner_news_fkey"),
        Index("idx_news_scope_partner_by_partner", "partner_id"),
        {"schema": "notification"},
    )

    news_id = mapped_column(BigInteger, nullable=False)
    partner_id = mapped_column(BigInteger, nullable=False)


class NewsScopeStation(Base):
    __tablename__ = "news_scope_station"
    __table_args__ = (
        PrimaryKeyConstraint("news_id", "id_grp", name="news_scope_station_pkey"),
        ForeignKeyConstraint(["news_id"], ["notification.news.id"], ondelete="CASCADE", name="news_scope_station_news_fkey"),
        Index("idx_news_scope_station_by_grp", "id_grp"),
        {"schema": "notification"},
    )

    news_id = mapped_column(BigInteger, nullable=False)
    id_grp = mapped_column(BigInteger, nullable=False)


class NewsScopeUser(Base):
    __tablename__ = "news_scope_user"
    __table_args__ = (
        PrimaryKeyConstraint("news_id", "user_id", name="news_scope_user_pkey"),
        ForeignKeyConstraint(["news_id"], ["notification.news.id"], ondelete="CASCADE", name="news_scope_user_news_fkey"),
        Index("idx_news_scope_user_by_user", "user_id"),
        {"schema": "notification"},
    )

    news_id = mapped_column(BigInteger, nullable=False)
    user_id = mapped_column(BigInteger, nullable=False)


class NewsReadReceipt(Base):
    __tablename__ = "news_read_receipt"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="news_read_receipt_pkey"),
        UniqueConstraint("news_id", "reader_role", "reader_id", name="uq_news_read_unique"),
        ForeignKeyConstraint(["news_id"], ["notification.news.id"], ondelete="CASCADE", name="news_read_receipt_news_fkey"),
        Index("idx_news_read_by_reader", "reader_role", "reader_id"),
        Index("idx_news_read_by_news", "news_id"),
        {"schema": "notification"},
    )

    id = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    news_id = mapped_column(BigInteger, nullable=False)
    reader_role = mapped_column(String(16), nullable=False)
    reader_id = mapped_column(BigInteger, nullable=False)
    read_at = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))


class Proposals(Base):
    __tablename__ = 'proposals'
    __table_args__ = (
        CheckConstraint('length(title) >= 1 AND length(title) <= 255', name='proposals_title_check'),
        ForeignKeyConstraint(['category_id'], ['notification.proposal_categories.id'], ondelete='RESTRICT', name='proposals_category_id_fkey'),
        ForeignKeyConstraint(['priority_id'], ['notification.proposal_priorities.id'], ondelete='RESTRICT', name='proposals_priority_id_fkey'),
        ForeignKeyConstraint(['status_id'], ['notification.proposal_statuses.id'], ondelete='RESTRICT', name='proposals_status_id_fkey'),
        PrimaryKeyConstraint('id', name='proposals_pkey'),
        Index('idx_proposals_created_at', 'created_at'),
        Index('idx_proposals_partner_id', 'partner_id'),
        Index('idx_proposals_status_id', 'status_id'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    partner_id = mapped_column(Integer, nullable=False)
    category_id = mapped_column(Integer, nullable=False)
    priority_id = mapped_column(Integer, nullable=False)
    status_id = mapped_column(Integer, nullable=False)
    title = mapped_column(Text, nullable=False)
    description = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    closed_at = mapped_column(DateTime(True))
    assigned_to_id = mapped_column(Integer)
    assigned_at = mapped_column(DateTime(True))
    closed_by = mapped_column(Integer)
    person_type = mapped_column(String(256), nullable=False, server_default=text("'partner'::character varying"))
    station_id = mapped_column(Integer)
    problem_user = mapped_column(Integer)

    category: Mapped['ProposalCategories'] = relationship('ProposalCategories', back_populates='proposals')
    priority: Mapped['ProposalPriorities'] = relationship('ProposalPriorities', back_populates='proposals')
    status: Mapped['ProposalStatuses'] = relationship('ProposalStatuses', back_populates='proposals')
    proposal_attachments: Mapped[List['ProposalAttachments']] = relationship('ProposalAttachments', uselist=True, back_populates='proposal')
    proposal_chat: Mapped[List['ProposalChat']] = relationship('ProposalChat', uselist=True, back_populates='proposal')


class ProposalAttachments(Base):
    __tablename__ = 'proposal_attachments'
    __table_args__ = (
        CheckConstraint('file_size_bytes >= 0 AND file_size_bytes <= 52428800', name='proposal_attachments_file_size_bytes_check'),
        ForeignKeyConstraint(['proposal_id'], ['notification.proposals.id'], ondelete='CASCADE', name='proposal_attachments_proposal_id_fkey'),
        PrimaryKeyConstraint('id', name='proposal_attachments_pkey'),
        UniqueConstraint('stored_filename', name='proposal_attachments_stored_filename_key'),
        Index('idx_attachments_proposal_id', 'proposal_id'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    proposal_id = mapped_column(Integer, nullable=False)
    original_filename = mapped_column(Text, nullable=False)
    stored_filename = mapped_column(Text, nullable=False)
    file_size_bytes = mapped_column(BigInteger, nullable=False)
    mime_type = mapped_column(String(100), nullable=False)
    file_path = mapped_column(Text, nullable=False)
    uploaded_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    proposal: Mapped['Proposals'] = relationship('Proposals', back_populates='proposal_attachments')


class ProposalChat(Base):
    __tablename__ = 'proposal_chat'
    __table_args__ = (
        ForeignKeyConstraint(['proposal_id'], ['notification.proposals.id'], ondelete='CASCADE', name='proposal_chat_proposal_id_fkey'),
        PrimaryKeyConstraint('msg_id', name='proposal_chat_pkey'),
        Index('idx_proposal_chat_proposal_id', 'proposal_id'),
        {'schema': 'notification'}
    )

    msg_id = mapped_column(BigInteger)
    proposal_id = mapped_column(BigInteger, nullable=False)
    user_id = mapped_column(Integer, nullable=False)
    date = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    text_ = mapped_column('text', Text, nullable=False)
    answer = mapped_column(Boolean, nullable=False)
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    read = mapped_column(Boolean, server_default=text('false'))
    read_at = mapped_column(DateTime(True))
    person_type = mapped_column(String(256), nullable=False, server_default=text("'partner'::character varying"))
    reply_to_msg_id = mapped_column(BigInteger, nullable=True)

    proposal: Mapped['Proposals'] = relationship('Proposals', back_populates='proposal_chat')
    proposal_chat_files: Mapped[List['ProposalChatFiles']] = relationship('ProposalChatFiles', uselist=True, back_populates='msg')

class ProposalChatReads(Base):
    __tablename__ = 'proposal_chat_reads'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'msg_id', 'person_type', name='proposal_chat_reads_pkey'),
        ForeignKeyConstraint(['msg_id'], ['notification.proposal_chat.msg_id'], ondelete='CASCADE', name='proposal_chat_reads_msg_id_fkey'),
        Index('idx_proposal_chat_reads_msg_id', 'msg_id'),
        Index('idx_proposal_chat_reads_user_id', 'user_id'),
        Index('idx_proposal_chat_reads_person_type', 'person_type'),
        {'schema': 'notification'}
    )

    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    msg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    read_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    person_type: Mapped[str] = mapped_column(String(256), nullable=False, server_default=text("'partner'::character varying"))

    

class ProposalChatFiles(Base):
    __tablename__ = 'proposal_chat_files'
    __table_args__ = (
        ForeignKeyConstraint(['msg_id'], ['notification.proposal_chat.msg_id'], ondelete='CASCADE', name='proposal_chat_files_msg_id_fkey'),
        PrimaryKeyConstraint('id', name='proposal_chat_files_pkey'),
        Index('idx_proposal_chat_files_msg_id', 'msg_id'),
        {'schema': 'notification'}
    )

    id = mapped_column(BigInteger)
    msg_id = mapped_column(BigInteger, nullable=False)
    file_path = mapped_column(Text, nullable=False)
    original_filename = mapped_column(Text, nullable=True)
    file_size_bytes = mapped_column(BigInteger, nullable=True)
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    msg: Mapped['ProposalChat'] = relationship('ProposalChat', back_populates='proposal_chat_files')
