from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
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


class SkystreamUsersLogs(Base):
    """Логи активных действий операторов (users.skystream_users_logs)."""

    __tablename__ = "skystream_users_logs"
    __table_args__ = (
        CheckConstraint(
            "(action = upper(action)) AND (length(action) > 0)",
            name="skystream_users_logs_action_check",
        ),
        Index("idx_skystream_users_logs_action", "action"),
        Index("idx_skystream_users_logs_created_at", "created_at"),
        Index("idx_skystream_users_logs_entity", "entity_type", "entity_id"),
        Index("idx_skystream_users_logs_project_id_created_at", "project_id", "created_at"),
        Index("idx_skystream_users_logs_user_id_created_at", "user_id", "created_at"),
        Index("idx_skystream_users_logs_success_created_at", "success", "created_at"),
        {
            "schema": "users",
            "comment": "Логи активных действий операторов (UPDATE/DELETE/REMOVE/…) по всем проектам Skystream",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="ID оператора (FK users.skystream_users)"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Проект, в котором совершено действие (FK users.skystream_projects)",
    )
    page: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Страница/экран UI, где совершено действие (не вкладка)",
    )
    action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Тип действия в верхнем регистре: UPDATE, DELETE, REMOVE, CREATE, …",
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="true — действие выполнено успешно, false — ошибка",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    entity_type: Mapped[Optional[str]] = mapped_column(
        Text, comment="Тип затронутой сущности (user, tariff, ticket, …)"
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        Text, comment="ID затронутой сущности (text — int/uuid/составной ключ)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, comment="Краткое человекочитаемое описание действия"
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Структурированный контекст: before/after, payload, доп. поля"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="Текст ошибки при success = false"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(INET, comment="IP клиента")
    user_agent: Mapped[Optional[str]] = mapped_column(Text, comment="User-Agent клиента")
    http_method: Mapped[Optional[str]] = mapped_column(
        Text, comment="HTTP-метод API-запроса (POST/PUT/PATCH/DELETE), если применимо"
    )
    request_path: Mapped[Optional[str]] = mapped_column(
        Text, comment="Путь API/эндпоинта (если отличается от page)"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        Text, comment="Корреляционный ID запроса для трассировки между сервисами"
    )
