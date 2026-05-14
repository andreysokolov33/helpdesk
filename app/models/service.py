from sqlalchemy import BigInteger, Boolean, DateTime, Double, Enum, Float, Index, Integer, Numeric, PrimaryKeyConstraint, Sequence, SmallInteger, String, Text, UniqueConstraint, text
from sqlalchemy.orm import mapped_column

from app.database import Base


class ActivatedDops(Base):
    __tablename__ = 'activated_dops'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9495731_primary'),
        Index('activated_dops_bort_idx', 'bort'),
        Index('activated_dops_dop_id_idx', 'dop_name'),
        Index('activated_dops_id_grp_idx', 'id_grp'),
        Index('activated_dops_uid_idx', 'uid'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(BigInteger, nullable=False)
    dop_name = mapped_column(String(64), nullable=False)
    activation_timestamp = mapped_column(
        DateTime, server_default=text('CURRENT_TIMESTAMP'))
    price = mapped_column(Numeric(10, 2))
    id_grp = mapped_column(Integer)
    bort = mapped_column(Integer)


class ActivatedServices(Base):
    __tablename__ = 'activated_services'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_949573_primary'),
        Index('activated_services_bort_idx', 'bort'),
        Index('activated_services_id_grp_idx', 'id_grp'),
        Index('activated_services_sname_idx', 'sname'),
        Index('activated_services_uid_idx', 'uid'),
        Index('idx_as2_dates', 'activation_timestamp', 'deactivation_date'),
        Index('idx_as2_uid_station_active', 'uid', 'id_grp',
              'activation_timestamp', 'deactivation_date'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    uid = mapped_column(BigInteger, nullable=False)
    activation_timestamp = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    days = mapped_column(Integer)
    packet_size = mapped_column(BigInteger)
    sname = mapped_column(String)
    price = mapped_column(Numeric(10, 2))
    id_grp = mapped_column(Integer)
    bort = mapped_column(Integer)
    deactivation_date = mapped_column(DateTime(timezone=True))


class AutoRenew(Base):
    __tablename__ = 'auto_renew'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90254_primary'),
        Index('idx_90254_id_unique', 'id', unique=True),
        Index('idx_auto_renew_lower_login', 'login', unique=True),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    login = mapped_column(String(255), nullable=False)
    service_name = mapped_column(String(255), nullable=False)
    days = mapped_column(Integer)
    volume = mapped_column(BigInteger)
    price = mapped_column(Numeric(10, 2))


class Dops(Base):
    __tablename__ = 'dops'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90328_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    price = mapped_column(BigInteger, nullable=False,
                          server_default=text("'0'::bigint"))
    title = mapped_column(
        String(256), server_default=text('NULL::character varying'))
    params = mapped_column(Text)
    ip_groups = mapped_column(Text)
    rules = mapped_column(Text)
    service = mapped_column(
        String(128), server_default=text('NULL::character varying'))


class LkTariffsLimited(Base):
    __tablename__ = 'lk_tariffs_limited'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90448_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    volume = mapped_column(BigInteger)
    price = mapped_column(BigInteger)
    speed = mapped_column(BigInteger)
    bort = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    name_tariff = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    sname = mapped_column(
        String(30), server_default=text('NULL::character varying'))
    range_b = mapped_column(String(10))


class LkTariffsUnlimited(Base):
    __tablename__ = 'lk_tariffs_unlimited'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90456_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    days = mapped_column(BigInteger)
    volume = mapped_column(BigInteger)
    price = mapped_column(BigInteger)
    speed_unlimited = mapped_column(BigInteger)
    speed_limited = mapped_column(BigInteger)
    range_b = mapped_column(
        String(10), server_default=text('NULL::character varying'))
    name_tariff = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    sname = mapped_column(
        String(30), server_default=text('NULL::character varying'))


class SliderTariffsLimited(Base):
    __tablename__ = 'slider_tariffs_limited'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='slider_tariffs_limited_pkey'),
        Index('idx_slider_tariffs_limited_service_id', 'service_id'),
        Index('idx_slider_tariffs_limited_satellite_id', 'satellite_id'),
        Index('idx_slider_tariffs_limited_sname', 'sname'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    plan_id = mapped_column(BigInteger, nullable=False)
    service_id = mapped_column(BigInteger, nullable=False)
    sname = mapped_column(String(100), nullable=False)
    satellite_id = mapped_column(Integer, nullable=False)
    volume_mb = mapped_column(BigInteger, nullable=False)
    price = mapped_column(Numeric(10, 2), nullable=False)
    active = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class SliderTariffsUnlimited(Base):
    __tablename__ = 'slider_tariffs_unlimited'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='slider_tariffs_unlimited_pkey'),
        Index('idx_slider_tariffs_unlimited_service_id', 'service_id'),
        Index('idx_slider_tariffs_unlimited_satellite_id', 'satellite_id'),
        Index('idx_slider_tariffs_unlimited_sname', 'sname'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    plan_id = mapped_column(BigInteger, nullable=False)
    service_id = mapped_column(BigInteger, nullable=False)
    sname = mapped_column(String(100), nullable=False)
    satellite_id = mapped_column(Integer, nullable=False)
    volume_mb = mapped_column(BigInteger, nullable=False)
    days = mapped_column(Integer, nullable=False)
    price = mapped_column(Numeric(10, 2), nullable=False)
    active = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class SliderTariffPlan(Base):
    __tablename__ = 'slider_tariff_plan'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='slider_tariff_plan_pkey'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    plan_name = mapped_column(String(200), nullable=False)
    status = mapped_column(String(20), nullable=False, server_default=text("'draft'::character varying"))
    effective_from = mapped_column(DateTime(timezone=True))
    effective_to = mapped_column(DateTime(timezone=True))
    description = mapped_column(Text)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class PricePer1Mb(Base):
    __tablename__ = 'price_per_1_mb'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_9495712331_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    id_hotspot = mapped_column(BigInteger, nullable=False)
    price = mapped_column(Numeric(10, 2))


class Service(Base):
    __tablename__ = 'service'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_94957_primary'),
        Index('service_type_idx', 'type'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    desc = mapped_column(Text, nullable=False,
                         comment='Описание тарифа. Отображается в ЛК абонента.')
    type = mapped_column(Enum('default', 'unlim_fap', name='service_type'), nullable=False, server_default=text(
        "'default'::service_type"), comment='Тип тарифа\r\ndefault - лимитный тариф\r\nunlim_fap - безлимитный')
    limit2 = mapped_column(BigInteger, nullable=False)
    hidden = mapped_column(SmallInteger, nullable=False, server_default=text(
        "'0'::smallint"), comment='Если 1, тариф не будет отображаться в ЛК абонента.')
    rate_limit = mapped_column(String(30), nullable=False)
    burst_rate = mapped_column(String(30), nullable=False)
    burst_threshold = mapped_column(String(30), nullable=False)
    burst_time = mapped_column(String(30), nullable=False)
    uptime_limit = mapped_column(String(30), nullable=False)
    uptime_used = mapped_column(String(30), nullable=False)
    sort = mapped_column(BigInteger, nullable=False)
    connect_disabled = mapped_column(SmallInteger, nullable=False)
    time_limit = mapped_column(BigInteger, nullable=False)
    active = mapped_column(SmallInteger, nullable=False,
                           server_default=text("'1'::smallint"))
    turbo_show = mapped_column(
        SmallInteger, nullable=False, server_default=text("'1'::smallint"))
    fap_id = mapped_column(SmallInteger, nullable=False,
                           server_default=text("'0'::smallint"))
    discount = mapped_column(Boolean, nullable=False,
                             server_default=text('false'))
    name = mapped_column(String(100), server_default=text(
        'NULL::character varying'), comment='Название тарифа. Отображается в ЛК абнента.')
    price = mapped_column(Double(53), comment='Цена тарифа')
    p_speed = mapped_column(String(20), server_default=text(
        'NULL::character varying'), comment='Заявление стоимость (Только для отображения)')
    limit = mapped_column(BigInteger)
    sname = mapped_column(String(100), server_default=text(
        'NULL::character varying'), comment='Основной идентификатор тарифа')
    sname_second = mapped_column(String(100), server_default=text(
        'NULL::character varying'), comment='Дополнительный идентификатор тарифа (При заморозке/ограничении)')
    sname_third = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    dops = mapped_column(
        Text, comment='Список идентификаторов доп.услуг. (См. service')
    speed = mapped_column(
        String(20), server_default=text('NULL::character varying'))
    parent_id = mapped_column(BigInteger)
    lft = mapped_column(BigInteger)
    rgt = mapped_column(BigInteger)
    depth = mapped_column(BigInteger)
    unlim = mapped_column(Integer)
    speed_fwd_mb = mapped_column(
        Integer, comment='Скорость в прямом канале, Мб')
    speed_rtn_mb = mapped_column(
        Float, comment='Скорость в обратном канале, Мб')
    slider = mapped_column(Integer, server_default=text('0'))
    frozen = mapped_column(Boolean, nullable=False,
                           server_default=text('false'))
    real_type = mapped_column(String(100))
    freq_range = mapped_column(String(16))
    full_permission = mapped_column(
        Boolean, nullable=False, server_default=text('false'))
    test_service = mapped_column(
        Boolean, nullable=False, server_default=text('false'))
    display_in_abs = mapped_column(
        Boolean, nullable=False, server_default=text('true'))
    display_in_selectors = mapped_column(
        Boolean, nullable=False, server_default=text('true'))
    for_skystream = mapped_column(
        Boolean, nullable=False, server_default=text('false'))


class ServiceDops(Base):
    __tablename__ = 'service_dops'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90818123_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    service_id = mapped_column(Integer)
    dops_id = mapped_column(Integer)


class ServiceGroups (Base):
    __tablename__ = 'service_groups'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90818_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    name = mapped_column(
        String(50), server_default=text('NULL::character varying'))
    type = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    rate = mapped_column(
        String(255), server_default=text('NULL::character varying'))
    u_slow_rate = mapped_column(
        String(255), server_default=text('NULL::character varying'))


class ServiceJur(Base):
    __tablename__ = 'service_jur'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90829_primary'),
        Index('idx_90829_service_jur_id_uindex', 'id', unique=True),
        {'schema': 'service'}
    )

    service = mapped_column(String(255), nullable=False)
    normal_traffic = mapped_column(BigInteger, nullable=False)
    extra_traffic = mapped_column(BigInteger, nullable=False)
    id = mapped_column(BigInteger)
    turbo_items = mapped_column(BigInteger)


class ServiceJurByMonths(Base):
    """Расписание ЮЛ по месяцам; перерасход в МБ — dop_consumption, цена МБ — cost_dop."""

    __tablename__ = 'service_jur_by_months'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90834_primary'),
        UniqueConstraint(
            'user_id', 'month', 'year', name='uk_service_jur_by_months_user_month_year'
        ),
        Index('service_jur_by_months_user2_id_idx', 'user_id', 'year', 'month'),
        Index('service_jur_by_months_user3_id_idx', 'user_id', 'year'),
        Index('service_jur_by_months_user_id_idx', 'user_id'),
        Index('service_jur_by_months_year_idx', 'year'),
        Index('service_jur_by_months_year_month_idx', 'year', 'month'),
        {'comment': 'Генерация закрывающих счетов', 'schema': 'service'}
    )

    id = mapped_column(BigInteger, autoincrement=True)
    month = mapped_column(BigInteger, nullable=False)
    sname = mapped_column(String(100), nullable=False)
    user_id = mapped_column(BigInteger)
    year = mapped_column(BigInteger)
    description = mapped_column(Text)
    was_dop_traffic = mapped_column(Boolean, server_default=text('false'))
    frozen = mapped_column(Boolean)
    freeze_date = mapped_column(DateTime(timezone=True))
    dop_volue = mapped_column(BigInteger)
    dop_consumption = mapped_column(BigInteger, server_default=text('0'))
    main_volue = mapped_column(BigInteger)
    unfreeze_date = mapped_column(DateTime(timezone=True))
    cost_main = mapped_column(Numeric(10, 2))
    cost_dop = mapped_column(Numeric(10, 2))


class TariffBucketPrice(Base):
    __tablename__ = 'tariff_bucket_price'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_908867_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(Integer, Sequence(
        'tariff_bucket_price_new_id_seq', schema='service'))
    station = mapped_column(
        String(10), server_default=text('NULL::character varying'))
    bucket = mapped_column(
        String(10), server_default=text('NULL::character varying'))
    price = mapped_column(BigInteger)


class TariffDatelecom(Base):
    __tablename__ = 'tariff_datelecom'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90910_primary'),
        {'schema': 'service'}
    )

    id = mapped_column(BigInteger)
    volume = mapped_column(BigInteger, nullable=False)
    cost = mapped_column(Double(53))
    name_tariff = mapped_column(
        String(100), server_default=text('NULL::character varying'))
    limited_speed_in_forward_channel = mapped_column(Integer)
    limited_speed_in_reverse_channel = mapped_column(Integer)
    unlimited_speed_in_forward_channel = mapped_column(Integer)
    unlimited_speed_in_reverse_channel = mapped_column(Integer)
    days = mapped_column(
        String(10), server_default=text('NULL::character varying'))
    lim_or_unlim = mapped_column(
        String(100), server_default=text('NULL::character varying'))
