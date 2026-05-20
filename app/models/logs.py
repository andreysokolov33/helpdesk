from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.users import Base


class HelpdeskOperatorLog(Base):
    __tablename__ = "helpdesk_operator_log"
    __table_args__ = (
        Index("idx_helpdesk_operator_log_created_at", "created_at"),
        Index("idx_helpdesk_operator_log_operator_created", "operator_id", "created_at"),
        Index("idx_helpdesk_operator_log_subscriber_created", "subscriber_id", "created_at"),
        Index("idx_helpdesk_operator_log_action_created", "action", "created_at"),
        {"schema": "logs"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.skystream_users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    page: Mapped[Optional[str]] = mapped_column(String(512))
    subscriber_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('users.user.id', ondelete="SET NULL")
    )
    subject_type: Mapped[Optional[str]] = mapped_column(String(64))
    subject_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    password_reset_code_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.password_reset_code.id", ondelete="SET NULL"),
    )
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    http_method: Mapped[Optional[str]] = mapped_column(String(16))
    request_path: Mapped[Optional[str]] = mapped_column(String(1024))
    client_ip: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
