from sqlalchemy import BigInteger, CHAR, Date, DateTime, Double, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.orm import mapped_column

from app.database import Base


class NetflowTraffic(Base):
    __tablename__ = 'netflow_traffic'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91275_primary'),
        Index('netflow_traffic_connect_type_idx', 'connect_type'),
        Index('netflow_traffic_date_idx', 'date'),
        Index('netflow_traffic_id_grp_idx', 'id_grp'),
        {'schema': 'traffic'}
    )

    id = mapped_column(BigInteger)
    id_grp = mapped_column(Integer, nullable=False)
    connect_type = mapped_column(String(10), server_default=text('NULL::character varying'))
    direction = mapped_column(String(10), server_default=text('NULL::character varying'))
    mb = mapped_column(BigInteger)
    date = mapped_column(Date)
    satellite = mapped_column(String)

class RadacctHistoryEveryDay(Base):
    __tablename__ = 'radacct_history_every_day'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91297_primary'),
        Index('idx_rhed_station_date', 'id_grp', 'date'),
        Index('radacct_history_every_day_date_idx', 'date'),
        Index('radacct_history_every_day_id_grp_idx', 'id_grp'),
        Index('radacct_history_every_day_protocol_idx', 'protocol'),
        Index('radacct_history_every_day_satellite_idx', 'satellite'),
        Index('radacct_history_every_day_username_idx', 'username'),
        {'schema': 'traffic'}
    )

    id = mapped_column(BigInteger)
    date = mapped_column(Date)
    username = mapped_column(CHAR(64), server_default=text('NULL::bpchar'))
    mb = mapped_column(Double(53))
    protocol = mapped_column(String(12), server_default=text('NULL::character varying'))
    upload = mapped_column(BigInteger)
    download = mapped_column(BigInteger)
    id_grp = mapped_column(Integer)
    satellite = mapped_column(String)


class RadacctHistoryEveryHour(Base):
    __tablename__ = 'radacct_history_every_hour'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91297_hour_primary'),
        Index('radacct_history_every_date_username_idx', 'username', 'date'),
        Index('radacct_history_every_hour_date_idx', 'date'),
        Index('radacct_history_every_hour_date_username_idx', 'date', 'hour', 'username'),
        Index('radacct_history_every_hour_username_idx', 'username'),
        {'schema': 'traffic'}
    )

    id = mapped_column(BigInteger)
    username = mapped_column(String(64), nullable=False)
    date = mapped_column(Date)
    hour = mapped_column(Integer, comment='Время по МСК')
    mb = mapped_column(Double(53))
    protocol = mapped_column(String(12), server_default=text('NULL::character varying'))
    upload = mapped_column(Double(53))
    download = mapped_column(Double(53))


class UserNetflow(Base):
    __tablename__ = 'user_netflow'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_91078_primary'),
        Index('user_netflow_netflow_name_idx', 'netflow_name'),
        {'schema': 'traffic'}
    )

    id = mapped_column(BigInteger)
    netflow_name = mapped_column(String(255), server_default=text('NULL::character varying'))
    traffic_in = mapped_column(BigInteger)
    traffic_out = mapped_column(BigInteger)
    date = mapped_column(DateTime(True))
