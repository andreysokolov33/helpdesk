from sqlalchemy import BigInteger, CHAR, Column, Date, DateTime, Index, Integer, PrimaryKeyConstraint, String, Table, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import mapped_column

from app.database import Base
metadata = Base.metadata


class CallSysLog(Base):
    __tablename__ = 'call_sys_log'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='call_sys_log_pkey'),
        Index('call_sys_log_date_idx', 'date'),
        Index('idx_prc', 'prc'),
        Index('idx_username', 'username'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    cmd = mapped_column(String(512))
    datum = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    date = mapped_column(Date, server_default=text('(CURRENT_TIMESTAMP)::date'))
    time = mapped_column(Time, server_default=text('(CURRENT_TIMESTAMP)::time without time zone'))
    result = mapped_column(Text)
    prc = mapped_column(Integer, server_default=text('0'))
    prc_datum = mapped_column(DateTime)
    username = mapped_column(String(50))
    script = mapped_column(String(256))
    ip_address = mapped_column(INET)


class Nas(Base):
    __tablename__ = 'nas'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91493_primary'),
        Index('idx_91493_nasname', 'nasname'),
        Index('nas_type_idx', 'type'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    nasname = mapped_column(String(128), nullable=False)
    secret = mapped_column(String(60), nullable=False, server_default=text("'secret'::character varying"))
    shortname = mapped_column(String(32), server_default=text('NULL::character varying'))
    type = mapped_column(String(30), server_default=text("'other'::character varying"))
    ports = mapped_column(Integer)
    server = mapped_column(String(64), server_default=text('NULL::character varying'))
    community = mapped_column(String(50), server_default=text('NULL::character varying'))
    description = mapped_column(String(200), server_default=text("'RADIUS Client'::character varying"))
    station_id = mapped_column(Integer, nullable=True)

class Radacct(Base):
    __tablename__ = 'radacct'
    __table_args__ = (
        PrimaryKeyConstraint('radacctid', name='radacct_pkey'),
        UniqueConstraint('acctuniqueid', name='radacct_acctuniqueid_key'),
        Index('idx_radacct_username_start_and_stop_time', 'acctstarttime', 'acctstoptime'),
        Index('radacct_acctstoptime_idx', 'acctstoptime'),
        Index('radacct_active_session_idx', 'acctuniqueid'),
        Index('radacct_bulk_close', 'nasipaddress', 'acctstarttime'),
        Index('radacct_radacctid_idx', 'radacctid'),
        Index('radacct_start_user_idx', 'acctstarttime', 'username'),
        Index('radacct_username_and_time_idx', 'username', 'acctstarttime', 'acctstoptime'),
        Index('radacct_username_idx', 'username'),
        {'schema': 'radius'}
    )

    radacctid = mapped_column(BigInteger)
    acctsessionid = mapped_column(Text, nullable=False)
    acctuniqueid = mapped_column(Text, nullable=False)
    nasipaddress = mapped_column(INET, nullable=False)
    username = mapped_column(Text)
    groupname = mapped_column(Text)
    realm = mapped_column(Text)
    nasportid = mapped_column(Text)
    nasporttype = mapped_column(Text)
    acctstarttime = mapped_column(DateTime(True))
    acctupdatetime = mapped_column(DateTime(True))
    acctstoptime = mapped_column(DateTime(True))
    acctinterval = mapped_column(BigInteger)
    acctsessiontime = mapped_column(BigInteger)
    acctauthentic = mapped_column(Text)
    connectinfo_start = mapped_column(Text)
    connectinfo_stop = mapped_column(Text)
    acctinputoctets = mapped_column(BigInteger)
    acctoutputoctets = mapped_column(BigInteger)
    calledstationid = mapped_column(Text)
    callingstationid = mapped_column(Text)
    acctterminatecause = mapped_column(Text)
    servicetype = mapped_column(Text)
    framedprotocol = mapped_column(Text)
    framedipaddress = mapped_column(INET)
    station_id = mapped_column(Integer)


class Radcheck(Base):
    __tablename__ = 'radcheck'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91531_primary'),
        Index('idx_32827_attribute', 'attribute'),
        Index('idx_32827_username', 'username'),
        Index('idx_32827_value', 'value'),
        Index('idx_91531_attribute', 'attribute'),
        Index('idx_91531_username', 'username'),
        Index('idx_91531_value', 'value'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    username = mapped_column(String(64), nullable=False, server_default=text("''::character varying"))
    attribute = mapped_column(String(64), nullable=False, server_default=text("''::character varying"))
    op = mapped_column(CHAR(2), nullable=False, server_default=text("'=='::bpchar"))
    value = mapped_column(String(253), nullable=False, server_default=text("''::character varying"))


class Radgroupcheck(Base):
    __tablename__ = 'radgroupcheck'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91540_primary'),
        Index('idx_91540_groupname', 'groupname'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    groupname = mapped_column(String(64), nullable=False)
    attribute = mapped_column(String(64), nullable=False)
    op = mapped_column(CHAR(2), nullable=False, server_default=text("'=='::bpchar"))
    value = mapped_column(String(253), nullable=False)


class Radgroupreply(Base):
    __tablename__ = 'radgroupreply'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91546_primary'),
        Index('idx_91546_groupname', 'groupname'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    groupname = mapped_column(String(64), nullable=False)
    attribute = mapped_column(String(64), nullable=False)
    op = mapped_column(CHAR(2), nullable=False, server_default=text("'='::bpchar"))
    value = mapped_column(String(253), nullable=False)
    fap_id = mapped_column(BigInteger)


class Radreply(Base):
    __tablename__ = 'radreply'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91552_primary'),
        Index('idx_91552_op', 'op'),
        Index('idx_91552_username', 'username'),
        Index('idx_91552_value', 'value'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    username = mapped_column(String(64), nullable=False, server_default=text("''::character varying"))
    attribute = mapped_column(String(64), nullable=False, server_default=text("''::character varying"))
    op = mapped_column(CHAR(2), nullable=False, server_default=text("'='::bpchar"))
    value = mapped_column(String(253), nullable=False, server_default=text("''::character varying"))
    full_packet = mapped_column(String(253))


class RadreplyUnlim(Base):
    __tablename__ = 'radreply_unlim'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_radreply_unlim_prm'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(Integer, nullable=False)
    now_day_traffic = mapped_column(BigInteger, server_default=text('0'))
    now_day_traffic_lastdate = mapped_column(BigInteger)
    full_packet = mapped_column(BigInteger)


class RadUserGroup(Base):
    __tablename__ = 'radusergroup'
    __table_args__ = {'schema': 'radius'}

    # Помечаем username как primary_key для корректной работы ORM
    username = mapped_column(String(64), primary_key=True, server_default=text("''"))
    groupname = mapped_column(String(64), nullable=False, server_default=text("''"))
    priority = mapped_column(BigInteger, nullable=False, server_default=text('1'))
    sname = mapped_column(String(64), comment='Соответствует sname в service')
    was_frozen = mapped_column(Integer, server_default=text('0'))
    frozen_now = mapped_column(Integer, server_default=text('0'))


class WrongHotspotAuth(Base):
    __tablename__ = 'wrong_hotspot_auth'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91574_primary'),
        {'schema': 'radius'}
    )

    id = mapped_column(BigInteger)
    datum = mapped_column(DateTime(True))
    username = mapped_column(String(128), server_default=text('NULL::character varying'))
