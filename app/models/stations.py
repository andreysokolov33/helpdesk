from dataclasses import Field
from typing import Optional
from sqlalchemy import (BigInteger, Boolean, ColumnDefault, Date, DateTime, Enum, Float, Index, Integer,
                        Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, text, ForeignKey)
from sqlalchemy.dialects.postgresql import CIDR, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from sqlalchemy.dialects.postgresql import MACADDR
from datetime import datetime, timezone

class AlivenessStatus(Base):
    __tablename__ = 'aliveness_status'
    __table_args__ = (
        PrimaryKeyConstraint('station_id', name='aliveness_status_pkey'),
        {'schema': 'stations'}
    )

    station_id = mapped_column(Integer)
    is_alive = mapped_column(Boolean, nullable=False, server_default=text('false'))
    updated_at = mapped_column(DateTime, server_default=text('now()'))


class Hotspot(Base):
    __tablename__ = 'hotspot'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94530123_primary'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column(String(45), server_default=text('NULL::character varying'))
    ip = mapped_column(String(45), server_default=text('NULL::character varying'))
    pool_hotspot = mapped_column(String(45))
    pool_pppoe = mapped_column(String(45))
    frequency = mapped_column(String(64))
    hub = mapped_column(String)
    vno = mapped_column(Integer)
    channel_id = mapped_column(Integer)
    active = mapped_column(Boolean, server_default=text('true'), comment='В работе ли данный пул или нет')


class IpGroupChannel(Base):
    __tablename__ = 'ip_group_channel'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9456079_primary'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column(String(50), server_default=text('NULL::character varying'))
    name_local = mapped_column(String(255), server_default=text('NULL::character varying'))
    operator_id = mapped_column(BigInteger)
    count_stat = mapped_column(Boolean, server_default=text('true'), comment='Для станций Скайстрим. Надо ли учитывать канал в статистике')
    satellite = mapped_column(String(50), server_default=text('NULL::character varying'))
    has_kpr = mapped_column(Boolean, server_default=text('true'))

class KprHistory(Base):
    __tablename__ = 'kpr_history'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='id'),
        Index('kpr_history_date_idx', 'date'),
        Index('kpr_history_station_date_desc_idx', 'station_id', 'date'),
        Index('kpr_history_station_id_idx', 'station_id'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    station_id = mapped_column(BigInteger, nullable=False)
    date = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    value = mapped_column(Numeric(5, 2), nullable=False)
    person = mapped_column(String(256))
    phone = mapped_column(String(256))
    comment = mapped_column(Text)


class StationFiles(Base):
    __tablename__ = 'station_files'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='station_files_pkey'),
        Index('idx_station_files_form_id', 'station_id'),
        Index('idx_station_files_type', 'file_type'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    station_id = mapped_column(BigInteger, nullable=False)
    file_type = mapped_column(String(32), nullable=False)
    file_url = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    sort_order = mapped_column(Integer)


class StationForms(Base):
    __tablename__ = 'station_forms'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='station_forms_pkey'),
        UniqueConstraint('partner', 'station_id', name='station_forms_unique'),
        Index('idx_station_forms_buc_serial', 'buc_serial'),
        Index('idx_station_forms_date_close', 'date_close'),
        Index('idx_station_forms_date_open', 'date_open'),
        Index('idx_station_forms_lat_lon', 'station_latitude', 'station_longitude'),
        Index('idx_station_forms_modem_mac', 'modem_mac'),
        Index('idx_station_forms_new_station', 'new_station'),
        Index('idx_station_forms_partner', 'partner'),
        Index('idx_station_forms_router_exists', 'router_exists'),
        Index('idx_station_forms_router_serial', 'router_serial'),
        Index('idx_station_forms_station_id', 'station_id'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    partner = mapped_column(BigInteger)
    name_installator = mapped_column(String(256))
    station_id = mapped_column(BigInteger)
    station_name = mapped_column(String(256))
    station_latitude = mapped_column(Numeric(10, 7))
    station_longitude = mapped_column(Numeric(10, 7))
    station_address = mapped_column(String(256))
    date_open = mapped_column(DateTime)
    date_close = mapped_column(DateTime)
    station_master = mapped_column(String(256))
    station_master_phone = mapped_column(String(256))
    where_placed = mapped_column(String(256))
    building_type = mapped_column(String(256))
    router_exists = mapped_column(Boolean, server_default=text('true'))
    router_brand = mapped_column(String(256))
    router_serial = mapped_column(String(256))
    router_ethernet_length = mapped_column(BigInteger)
    modem_mac = mapped_column(String(256))
    modem_brand = mapped_column(String(256))
    modem_model = mapped_column(String(256))
    modem_coaxial_type = mapped_column(String(256))
    modem_coaxial_length = mapped_column(BigInteger)
    modem_lightning_arresters = mapped_column(Boolean)
    modem_grounding = mapped_column(Boolean)
    modem_ups = mapped_column(Boolean)
    buc_power = mapped_column(Integer)
    buc_brand = mapped_column(String(256))
    buc_serial = mapped_column(String(256))
    buc_model = mapped_column(String(256))
    buc_grounding = mapped_column(Boolean)
    lnb_brand = mapped_column(String(256))
    antenna_diameter = mapped_column(Integer)
    antenna_brand = mapped_column(String(256))
    new_station = mapped_column(Boolean, server_default=text('true'))
    lnb_serial = mapped_column(String(256))
    lnb_model = mapped_column(String(256))
    router_ethernet_type = mapped_column(String(256))
    modem_serial = mapped_column(String(256))
    center_station = mapped_column(Boolean, server_default=text('false'), comment='Станция с true у партнера будет выводиться в центре на карте в партнерском кабинете. Если несколько true, то первая из них')


class StationPhotos(Base):
    __tablename__ = 'station_photos'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='station_photos_pkey'),
        UniqueConstraint('file_path', name='uq_station_photos_file'),
        UniqueConstraint('thumb_path', name='uq_station_photos_thumb'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger)
    station_id = mapped_column(BigInteger, nullable=False)
    title = mapped_column(String(255), nullable=False, server_default=text("''::character varying"))
    file_path = mapped_column(Text, nullable=False)
    mime_type = mapped_column(String(100), nullable=False, server_default=text("'image/jpeg'::character varying"))
    created_at = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    thumb_path = mapped_column(Text)



class CcrAddresses(Base):
    __tablename__ = 'ccr_addresses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94425_primary'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(Integer)
    name = mapped_column(String(50), server_default=text('NULL::character varying'))
    ip_public = mapped_column(String(24), server_default=text('NULL::character varying'))
    ip_tunnel = mapped_column(String(24), server_default=text('NULL::character varying'))
    ip_rostelecom = mapped_column(String(24))
    ip_gks = mapped_column(String(24))
    city = mapped_column(String)


class GrpSrv(Base):
    __tablename__ = 'grp_srv'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94520_primary'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger)
    id_grp = mapped_column(BigInteger)
    id_srv = mapped_column(BigInteger)


class MediaServer(Base):
    __tablename__ = 'media_servers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='media_servers_pkey'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger, autoincrement=True)
    station_id = mapped_column(
        Integer,
        ForeignKey('wifitochka.ip_group.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
    )
    name = mapped_column(String(255), nullable=False)
    ip_address = mapped_column(INET, nullable=True)
    is_active = mapped_column(Boolean, nullable=True, server_default=text('true'))


class IpGroup(Base):
    __tablename__ = 'ip_group'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94538_primary_1'),
        Index('idx_99006_id_diler', 'id_diler'),
        Index('idx_99006_id_diler1', 'id_diler'),
        Index('idx_99006_ip_group_virtual_network_operator_fk', 'vno'),
        Index('idx_99006_ip_group_virtual_network_operator_fk1', 'vno'),
        {'comment': '1 - Тестовая группа для скриптов и проверок\r\n'
                '0 - Рабочая станция',
     'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger)
    id_diler = mapped_column(BigInteger, nullable=False)
    showms = mapped_column(BigInteger, nullable=False, server_default=text("'0'::bigint"))
    operators = mapped_column(Text, nullable=False)
    name = mapped_column(String(64), server_default=text('NULL::character varying'))
    vno = mapped_column(BigInteger, comment='VNO - Virtual Network Operator.')
    station = mapped_column(BigInteger)
    ip = mapped_column(String(20), server_default=text('NULL::character varying'))
    mask = mapped_column(String(20), server_default=text('NULL::character varying'))
    router_ip = mapped_column(String(64), server_default=text('NULL::character varying'))
    login = mapped_column(String(20), server_default=text('NULL::character varying'))
    pass_ = mapped_column('pass', String(20), server_default=text('NULL::character varying'))
    id_hotspot = mapped_column(BigInteger, server_default=text("'1'::bigint"))
    channel_id = mapped_column(BigInteger)
    message = mapped_column(Text)
    service_master = mapped_column(String(128), server_default=text('NULL::character varying'))
    gmt = mapped_column(Integer, server_default=text('3'))
    is_def = mapped_column(Integer)
    for_scripts = mapped_column(BigInteger)
    antenna_cm_ = mapped_column('antenna(cm)', Integer)
    region = mapped_column(Integer)
    dc = mapped_column(String(10), server_default=text('NULL::character varying'))
    district = mapped_column(String(64), server_default=text('NULL::character varying'))
    city = mapped_column(String(64), server_default=text('NULL::character varying'))
    street = mapped_column(String(64), server_default=text('NULL::character varying'))
    house = mapped_column(String(64), server_default=text('NULL::character varying'))
    active = mapped_column(Integer, server_default=text('1'))
    test_group = mapped_column(Integer, server_default=text('0'))
    network_hotspot = mapped_column(CIDR)
    network_pppoe = mapped_column(CIDR)
    modem = mapped_column(INET, comment='Адрес модема')
    rus_name = mapped_column(String(256))
    latitude = mapped_column(Numeric(10, 7))
    longitude = mapped_column(Numeric(10, 7))
    buc = mapped_column(Float)
    is_netflow = mapped_column(Boolean, server_default=text('false'))
    has_formular = mapped_column(Boolean, server_default=text('true'))
    global_partner_id = mapped_column(BigInteger)

class Regions(Base):
    __tablename__ = 'regions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94927_primary'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column(String(64), server_default=text('NULL::character varying'))


class VirtualNetworkOperator(Base):
    __tablename__ = 'virtual_network_operator'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_95251_primary'),
        {'comment': 'Виртуальный сетевой оператор. Куда направляются все платежи',
     'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column(String(100), server_default=text('NULL::character varying'))
    jur_info = mapped_column(Text)
    pay_info = mapped_column(Text)

class Satellite(Base):
    __tablename__ = 'satellites'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_945604379_primary'),
        {'schema': 'stations'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(
        String(50), 
        server_default=text('NULL::character varying')
    )
    freq_range: Mapped[Optional[str]] = mapped_column(
        String(16), 
        server_default=text('NULL::character varying')
    )
    active: Mapped[Optional[bool]] = mapped_column(
        Boolean, 
        server_default=text('true')
    )
    kp_file_name: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
        comment="Базовое имя шаблона КП (без .xml/.xslt), например KPTemplate_ku",
    )


class ChannelSatellite(Base):
    __tablename__ = 'channel_satellite'
    __table_args__ = (
        PrimaryKeyConstraint('channel_id', 'satellite_id', name='pk_ip_group_channel_satellite'),
        {'schema': 'stations'}
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('stations.ip_group_channel.id', ondelete='CASCADE'),
        primary_key=True
    )
    satellite_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('stations.satellites.id', ondelete='CASCADE'),
        primary_key=True
    )

class Equipment(Base):
    __tablename__ = 'equipment'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='equipment_new_pkey'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger, server_default=text("nextval('equipment_new_id_seq'::regclass)"))
    name = mapped_column(String(50))
    ipadd_1 = mapped_column(String(24))
    ipadd_2 = mapped_column(String(24))
    ipadd_3 = mapped_column(String(24))
    ip_tunnel = mapped_column(String(24))
    serial_number = mapped_column(String(100))
    model = mapped_column(String(100))
    vendor = mapped_column(String(100))
    mac_address = mapped_column(MACADDR)
    inventory_number = mapped_column(String(50))
    city = mapped_column(Text)
    address = mapped_column(Text)
    installation_date = mapped_column(Date)
    decommission_date = mapped_column(Date)
    last_config_update = mapped_column(DateTime)
    active = mapped_column(Boolean, server_default=text('true'))
    eng_city = mapped_column(Text)
    city_id = mapped_column(Integer)
    
    
class City(Base):
    __tablename__ = 'cities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94560796_primary'),
        {'schema': 'stations'}
    )
    
    id = mapped_column(BigInteger, primary_key=True)
    eng_name = mapped_column(String(50), nullable=True)
    rus_name = mapped_column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<City(id={self.id}, eng='{self.eng_name}', rus='{self.rus_name}')>"    
    
    
# Допустимые статусы задачи
TaskStatusEnum = Enum(
    'pending',
    'processing',
    'completed',
    'failed',
    name='task_status_enum',
    schema='wifitochka'  # если используешь схему
)

class SystemTask(Base):
    __tablename__ = 'system_tasks'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_system_tasks_pkey'),
        {'schema': 'wifitochka'}
    )

    id = mapped_column(BigInteger, primary_key=True)
    task_code = mapped_column(String(50), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at = mapped_column(DateTime(timezone=True), nullable=True)
    status = mapped_column(
        TaskStatusEnum,
        nullable=False,
        default=ColumnDefault('pending')
    )
    error_message = mapped_column(Text, nullable=True)

class OperationsType(Base):
    """Типы операций (справочник)"""
    __tablename__ = 'operations_type'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='operations_type_pkey'),
        Index('idx_operations_type_code', 'code'),
        Index('idx_operations_type_is_active', 'is_active'),
        {'schema': 'stations'}
    )

    id = mapped_column(Integer, autoincrement=True)
    name = mapped_column(String(100), nullable=False, unique=True)
    code = mapped_column(String(50), nullable=False, unique=True)
    description = mapped_column(Text)
    created_at = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    is_active = mapped_column(Boolean, nullable=False, server_default=text('true'))

    # Relationships
    operations = relationship('Operations', back_populates='operation_type_rel')


class Operations(Base):
    """Журнал операций по станциям"""
    __tablename__ = 'operations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='operations_pkey'),
        Index('idx_operations_station_id', 'station_id'),
        Index('idx_operations_author', 'author'),
        Index('idx_operations_operation_type', 'operation_type'),
        Index('idx_operations_date', 'date'),
        Index('idx_operations_created_at', 'created_at'),
        Index('idx_operations_station_date', 'station_id', 'date'),
        Index('idx_operations_author_date', 'author', 'date'),
        Index('idx_operations_type_date', 'operation_type', 'date'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger, autoincrement=True)
    station_id = mapped_column(Integer, ForeignKey('wifitochka.ip_group.id', ondelete='CASCADE'), nullable=False)
    author = mapped_column(Integer, nullable=False)
    who = mapped_column(Text, nullable=False)
    date = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    action = mapped_column(Text, nullable=False)
    operation_type = mapped_column(Integer, ForeignKey('stations.operations_type.id', ondelete='RESTRICT'), nullable=False)
    comment = mapped_column(Text)
    created_at = mapped_column(DateTime, nullable=False, server_default=text('now()'))

    # Relationships
    operation_type_rel = relationship('OperationsType', back_populates='operations')
    
class StationLayout(Base):
    __tablename__ = 'station_layouts'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='station_layouts_pkey'),
        {'schema': 'stations'}
    )

    id = mapped_column(BigInteger, primary_key=True)
    station_id = mapped_column(BigInteger, nullable=False, index=True)
    operator_id = mapped_column(BigInteger, nullable=False)  # Кто загрузил
    
    filename = mapped_column(String(255), nullable=False)    # Оригинальное имя (схема_от_мая.vsdx)
    file_path = mapped_column(Text, nullable=False)          # Путь на диске (stations/266/layouts/uuid.vsdx)
    file_size = mapped_column(BigInteger)                   # Размер в байтах
    mime_type = mapped_column(String(100))                  # Тип контента
    
    description = mapped_column(Text)                        # Краткое описание или заметка
    created_at = mapped_column(DateTime(True), server_default=text('now()'))
    
    # Флаг для логического удаления (опционально, но полезно для тех. доков)
    is_deleted = mapped_column(Boolean, server_default=text('false'))