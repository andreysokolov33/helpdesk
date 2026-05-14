from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Identity, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeedbackForm(Base):
    __tablename__ = "feedback_forms"
    __table_args__ = {"schema": "oss"}

    id: Mapped[int] = mapped_column(Identity(always=False), primary_key=True)
    fullname: Mapped[str] = mapped_column(String(255), nullable=False)
    mob_tel: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    additional: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default=text("true"))
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default=text("false"))
    date: Mapped[Optional[datetime]] = mapped_column(
        "date",
        DateTime(timezone=True),
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class FeedbackComment(Base):
    __tablename__ = "feedback_comments"
    __table_args__ = {"schema": "oss"}

    id: Mapped[int] = mapped_column(Identity(always=False), primary_key=True)
    feedback_id: Mapped[int] = mapped_column(nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default=text("true"))

