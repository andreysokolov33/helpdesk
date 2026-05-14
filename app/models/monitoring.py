from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Numeric,
    SmallInteger,
    Text,
    DateTime,
    Integer,
    String,
    ForeignKey,
    PrimaryKeyConstraint,
    UniqueConstraint,
    text,
    Index,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, relationship
from app.database import Base

# Существующий в БД тип monitoring.issue_status
issue_status_enum = ENUM(
    "NEW",
    "IN_PROGRESS",
    "RESOLVED_MANUAL",
    "RESOLVED_AUTO",
    "UNRESOLVED",
    "POSTPONED",
    name="issue_status",
    schema="monitoring",
    create_type=False,
)


class DaemonStatus(Base):
    __tablename__ = "daemon_status"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="daemon_status_pkey"),
        UniqueConstraint("service_name", name="daemon_status_service_name_key"),
        {"schema": "monitoring"},
    )

    id = mapped_column(Integer)
    service_name = mapped_column(String(100), nullable=False)
    service_name_ru = mapped_column(String(200), nullable=False)
    is_on = mapped_column(Boolean, nullable=False, server_default=text("false"))
    started_at = mapped_column(DateTime(True))
    checked_at = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    stopped_at = mapped_column(DateTime(True))


class Incident(Base):
    __tablename__ = 'incidents'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incidents_pkey'),
        Index(
            'idx_active_incidents_partial', 
            'user_id', 'type', 
            postgresql_where=text(
                "status = ANY (ARRAY['NEW'::monitoring.issue_status, "
                "'IN_PROGRESS'::monitoring.issue_status, "
                "'POSTPONED'::monitoring.issue_status])"
            )
        ),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    user_id = mapped_column(BigInteger, nullable=False)
    type = mapped_column(Text, nullable=False)
    severity = mapped_column(Integer, server_default=text('2'))
    description = mapped_column(Text)
    created_at = mapped_column(
        DateTime(True),
        server_default=text('now()')
    )
    last_seen_at = mapped_column(
        DateTime(True),
        server_default=text('now()')
    )
    resolved_at = mapped_column(DateTime(True))
    status = mapped_column(
        issue_status_enum,
        server_default=text("'NEW'::monitoring.issue_status"),
    )
    assigned_engineer_id = mapped_column(BigInteger)
    closing_engineer_id = mapped_column(BigInteger)
    login = mapped_column(String)

    # Связи (опционально)
    comments = relationship(
        "IncidentComment",
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    attachments = relationship(
        "IncidentAttachment",
        back_populates="incident",
        cascade="all, delete-orphan"
    )
    type_id = mapped_column(
        SmallInteger,
        ForeignKey('monitoring.incident_types.id')
    )

    # Связи (опционально)
    incident_type = relationship("IncidentType")
    views = relationship("IncidentView", back_populates="incident")


class IncidentComment(Base):
    __tablename__ = 'incident_comments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incident_comments_pkey'),
        Index('idx_comments_incident_id', 'incident_id'),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    incident_id = mapped_column(
        BigInteger,
        ForeignKey('monitoring.incidents.id', ondelete='CASCADE'),
        nullable=False
    )
    author_id = mapped_column(BigInteger)
    comment_text = mapped_column(Text, nullable=False)
    created_at = mapped_column(
        DateTime(True),
        server_default=text('now()')
    )

    # Связь
    incident = relationship("Incident", back_populates="comments")


class IncidentAttachment(Base):
    __tablename__ = 'incident_attachments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incident_attachments_pkey'),
        Index('idx_attachments_incident_id', 'incident_id'),
        Index('idx_attachments_comment_id', 'comment_id'),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    incident_id = mapped_column(
        BigInteger,
        ForeignKey('monitoring.incidents.id', ondelete='CASCADE'),
        nullable=False
    )
    comment_id = mapped_column(
        BigInteger,
        ForeignKey('monitoring.incident_comments.id', ondelete='SET NULL'),
        nullable=True
    )
    file_path = mapped_column(Text, nullable=False)
    file_name = mapped_column(Text, nullable=False)
    file_size = mapped_column(Integer)
    uploaded_by = mapped_column(BigInteger)
    created_at = mapped_column(
        DateTime(True),
        server_default=text('now()')
    )

    # Связь
    incident = relationship("Incident", back_populates="attachments")
    comment_id = mapped_column(BigInteger)


class Exclusion(Base):
    __tablename__ = 'exclusions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='exclusions_pkey'),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    entity_id = mapped_column(BigInteger, nullable=False)
    entity_type = mapped_column(Text, nullable=False)
    excluded_until = mapped_column(DateTime(True))
    reason = mapped_column(Text)
    created_at = mapped_column(
        DateTime(True),
        server_default=text('now()')
    )
    created_by = mapped_column(BigInteger)
    type_id = mapped_column(
        SmallInteger,
        ForeignKey('monitoring.incident_types.id')
    )

    # Связь
    incident_type = relationship("IncidentType")


class IncidentType(Base):
    __tablename__ = 'incident_types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incident_types_pkey'),
        UniqueConstraint('name', name='incident_types_name_key'),
        CheckConstraint(
            "entity_type = ANY (ARRAY['USER'::text, 'STATION'::text])",
            name='incident_types_entity_type_check'
        ),
        {'schema': 'monitoring'}
    )

    id = mapped_column(SmallInteger)
    name = mapped_column(Text, nullable=False)
    description = mapped_column(Text, nullable=False)
    entity_type = mapped_column(Text, nullable=False)

    # Связь
    exclusions = relationship("Exclusion", back_populates="incident_type")


# В классе Exclusion добавляем обратную связь
Exclusion.incident_type = relationship(
    "IncidentType",
    back_populates="exclusions"
)


class TopHistory(Base):
    __tablename__ = 'top_history'
    __table_args__ = (
        {'schema': 'monitoring'}
    )

    snapshot_date = mapped_column(Date, primary_key=True)
    uid = mapped_column(BigInteger, primary_key=True)
    total_paid = mapped_column(Numeric(15, 2))
    rank = mapped_column(Integer)


class TopActiveSubscriber(Base):
    __tablename__ = 'top_active_subscribers'
    __table_args__ = (
        PrimaryKeyConstraint('rank', name='top_active_subscribers_pkey'),
        UniqueConstraint('uid', name='top_active_subscribers_uid_key'),
        {'schema': 'monitoring'}
    )

    rank = mapped_column(
        Integer,
        primary_key=True,  # Уже есть PrimaryKeyConstraint, но можно указать и здесь
        autoincrement=True
    )
    uid = mapped_column(BigInteger, nullable=False)
    total_paid = mapped_column(Numeric(15, 2), nullable=False)
    updated_at = mapped_column(
        DateTime,
        server_default=text('now()')
    )

class IncidentView(Base):
    __tablename__ = 'incident_views'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incident_views_pkey'),
        UniqueConstraint('incident_id', 'engineer_id', name='idx_incident_views_unique'),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    incident_id = mapped_column(
        BigInteger,
        ForeignKey('monitoring.incidents.id', ondelete='CASCADE'),
        nullable=False
    )
    engineer_id = mapped_column(BigInteger, nullable=False)
    viewed_at = mapped_column(
        DateTime(True),
        server_default=text('now()'),
        nullable=False
    )

    incident = relationship("Incident", back_populates="views")


class TopStationsByPays(Base):
    """Топ станций по платежам (заполняется внешними скриптами)."""
    __tablename__ = 'top_stations_by_pays'
    __table_args__ = (
        PrimaryKeyConstraint('rank', name='top_total_pays_pkey'),
        UniqueConstraint('uid', name='top_total_pays_uid_key'),
        {'schema': 'monitoring'},
    )
    rank = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid = mapped_column(BigInteger, nullable=False)
    total_pays = mapped_column(Numeric(15, 2), nullable=False)
    updated_at = mapped_column(DateTime, server_default=text('now()'))


class TopStationsByTickets(Base):
    """Топ станций по проблемам/тикетам (заполняется внешними скриптами)."""
    __tablename__ = 'top_stations_by_tickets'
    __table_args__ = (
        PrimaryKeyConstraint('rank', name='top_total_tickets_pkey'),
        UniqueConstraint('uid', name='top_total_tickets_uid_key'),
        {'schema': 'monitoring'},
    )
    rank = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid = mapped_column(BigInteger, nullable=False)
    total_tickets = mapped_column(Numeric(15, 2), nullable=False)
    updated_at = mapped_column(DateTime, server_default=text('now()'))


class TopStationsByTrafficConsumption(Base):
    """Топ станций по трафику (заполняется внешними скриптами)."""
    __tablename__ = 'top_stations_by_traffic_consumption'
    __table_args__ = (
        PrimaryKeyConstraint('rank', name='top_traffic_consumption_pkey'),
        UniqueConstraint('uid', name='top_traffic_consumption_uid_key'),
        {'schema': 'monitoring'},
    )
    rank = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid = mapped_column(BigInteger, nullable=False)
    total_traffic = mapped_column(Numeric(15, 2), nullable=False)
    updated_at = mapped_column(DateTime, server_default=text('now()'))


class IncidentAssignment(Base):
    """Назначения партнёров и техников к автоматически обнаруженным инцидентам."""
    __tablename__ = 'incident_assignments'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='incident_assignments_pkey'),
        UniqueConstraint('incident_id', 'entity_type', 'entity_id', name='incident_assignments_unique'),
        CheckConstraint("entity_type IN ('partner', 'technician')", name='incident_assignments_entity_type_check'),
        Index('idx_incident_assignments_incident_id', 'incident_id'),
        {'schema': 'monitoring'}
    )

    id = mapped_column(BigInteger)
    incident_id = mapped_column(
        BigInteger,
        ForeignKey('monitoring.incidents.id', ondelete='CASCADE'),
        nullable=False
    )
    entity_type = mapped_column(String(20), nullable=False)
    entity_id = mapped_column(BigInteger, nullable=False)
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    created_by = mapped_column(BigInteger, nullable=True)