"""Модели notification — новости операторов helpdesk."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.users import Base


class HelpdeskOperatorNewsKind(str, Enum):
    general = "general"
    training = "training"
    alert = "alert"


class HelpdeskOperatorNewsImportance(str, Enum):
    normal = "normal"
    important = "important"
    featured = "featured"


_helpdesk_news_kind = ENUM(
    HelpdeskOperatorNewsKind,
    name="helpdesk_operator_news_kind",
    schema="notification",
    create_type=False,
)

_helpdesk_news_importance = ENUM(
    HelpdeskOperatorNewsImportance,
    name="helpdesk_operator_news_importance",
    schema="notification",
    create_type=False,
)


class HelpdeskOperatorNews(Base):
    __tablename__ = "helpdesk_operator_news"
    __table_args__ = (
        Index("idx_helpdesk_operator_news_published", "published_at", "id"),
        Index("idx_helpdesk_operator_news_kind", "kind"),
        {"schema": "notification"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    kind: Mapped[HelpdeskOperatorNewsKind] = mapped_column(
        _helpdesk_news_kind,
        nullable=False,
        server_default=text("'general'::notification.helpdesk_operator_news_kind"),
    )
    importance: Mapped[HelpdeskOperatorNewsImportance] = mapped_column(
        _helpdesk_news_importance,
        nullable=False,
        server_default=text("'normal'::notification.helpdesk_operator_news_importance"),
    )
    link_path: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.skystream_users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class HelpdeskOperatorNewsRead(Base):
    __tablename__ = "helpdesk_operator_news_read"
    __table_args__ = (
        UniqueConstraint("news_id", "operator_id", name="uq_helpdesk_operator_news_read_operator"),
        Index("idx_helpdesk_operator_news_read_operator", "operator_id", "read_at"),
        Index("idx_helpdesk_operator_news_read_news", "news_id"),
        {"schema": "notification"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notification.helpdesk_operator_news.id", ondelete="CASCADE"),
        nullable=False,
    )
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
