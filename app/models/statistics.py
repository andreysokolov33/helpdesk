from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, PrimaryKeyConstraint, Sequence, String, UniqueConstraint, text
from sqlalchemy.orm import mapped_column

from app.database import Base
metadata = Base.metadata


class Arppu(Base):
    __tablename__ = 'arppu'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90354_arrpu_primary'),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger, Sequence('arrpu_id_seq', schema='statistics'))
    pays = mapped_column(Numeric(10, 2))
    pays_count = mapped_column(BigInteger)
    users = mapped_column(BigInteger)
    yearmonth = mapped_column(String(10), server_default=text('NULL::character varying'))
    satellite = mapped_column(String(64), server_default=text('NULL::character varying'))
    arppu = mapped_column(Numeric(10, 2))
    freq = mapped_column(String(8))
    operator = mapped_column(String)
    bort = mapped_column(String)


class KprThresholds(Base):
    __tablename__ = 'kpr_thresholds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='kpr_thresholds_pkey'),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger)
    min_kpr = mapped_column(Integer, nullable=False)
    satellite = mapped_column(Integer)


class ModemModcods(Base):
    __tablename__ = 'modem_modcods'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='modem_modcods_pkey'),
        {'comment': 'Таблица для хранения информации о MODCOD, включая идентификатор, '
                'название и теоретическую спектральную эффективность (бит/Гц)',
     'schema': 'statistics'}
    )

    id = mapped_column(Integer, comment='Уникальный идентификатор MODCOD')
    name = mapped_column(String(50), nullable=False, comment='Название MODCOD (например, QPSK 1/4, 8PSK 3/4)')
    byte_gz = mapped_column(Numeric(5, 2), nullable=False, comment='Теоретическая спектральная эффективность в бит/Гц')


class MonthlyStationStats(Base):
    __tablename__ = 'monthly_station_stats'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='monthly_station_stats_pkey'),
        UniqueConstraint('station_id', 'yearmonth', name='uq_monthly_station_stats'),
        Index('idx_monthly_stats_station', 'station_id'),
        Index('idx_monthly_stats_station_yearmonth', 'station_id', 'yearmonth'),
        Index('idx_monthly_stats_yearmonth', 'yearmonth'),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger)
    station_id = mapped_column(Integer, nullable=False)
    yearmonth = mapped_column(Integer, nullable=False)
    revenue = mapped_column(Numeric(10, 2), comment='Сумма всех платежей ФЛ и ЮЛ за период')
    arpu = mapped_column(Numeric(10, 2), comment='Средний доход на пользователя. Формула: revenue / active_subscribers.')
    arppu = mapped_column(Numeric(10, 2), comment='Средний доход на платящего пользователя. Формула: revenue / COUNT(DISTINCT paying_abonent_id).')
    mrr = mapped_column(Numeric(10, 2), comment='Месячная повторяющаяся выручка - пропорциональная стоимость активных услуг')
    clv = mapped_column(Numeric(10, 2), comment='Пожизненная ценность клиента (arpu * avg_duration_months / churn_rate)')
    add_services_revenue = mapped_column(Numeric(10, 2), comment='Доход от дополнительных услуг (например, турбо-кнопки). Формула: SUM(amount) по доп. услугам.')
    profitability = mapped_column(Numeric(10, 2), comment='Рентабельность сделок. Формула: (revenue - total_costs) / revenue * 100, где total_costs — расходы на трафик/обслуживание.')
    active_subscribers = mapped_column(Integer, comment='Количество активных абонентов. Формула: COUNT(DISTINCT abonent_id) с активным тарифом хотя бы 1 день в месяце.')
    churn_rate = mapped_column(Numeric(10, 2), comment='Процент оттока. Формула: (отключенные_абоненты / active_subscribers_в_начале_месяца) * 100.')
    new_registrations = mapped_column(Integer, comment='Число новых регистраций. Формула: COUNT(DISTINCT abonent_id) с первым тарифом в месяце.')
    returned_subscribers = mapped_column(Integer, comment='Число вернувшихся абонентов. Формула: COUNT(DISTINCT abonent_id), у которых был тариф ранее, но после перерыва начался новый.')
    total_traffic = mapped_column(Numeric(10, 2), comment='Общий трафик (в ГБ). Формула: SUM(daily_traffic) по всем абонентам станции.')
    avg_traffic_per_sub = mapped_column(Numeric(10, 2), comment='Средний трафик на абонента. Формула: total_traffic / active_subscribers.')
    add_services_usage = mapped_column(Integer, comment='Количество использованных доп. услуг. Формула: COUNT(доп_услуги).')
    avg_bit_hz = mapped_column(Numeric(5, 2), comment='Средний Bit/Hz за месяц. Формула: AVG(bit_hz) по всем точкам, исключая downtime.')
    avg_signal = mapped_column(Numeric(5, 2), comment='Средний уровень сигнала за месяц. Формула: AVG(signal_level) по всем точкам, исключая downtime.')
    downtime_pct = mapped_column(Numeric(5, 2), comment='Процент времени за месяц, когда станция была не в сети (signal и byte_gz = NULL)')
    signal_good_pct = mapped_column(Numeric(5, 2), comment='% времени в хорошей зоне (сигнал). Формула: (COUNT(точек с signal_level > -70) / total_points) * 100.')
    signal_moderate_pct = mapped_column(Numeric(5, 2), comment='% времени в умеренной зоне (сигнал). Формула: (COUNT(точек с signal_level BETWEEN -90 AND -70) / total_points) * 100.')
    signal_serious_pct = mapped_column(Numeric(5, 2), comment='% времени в серьезной зоне (сигнал). Формула: (COUNT(точек с signal_level BETWEEN -110 AND -90) / total_points) * 100.')
    signal_critical_pct = mapped_column(Numeric(5, 2), comment='% времени в критической зоне (сигнал). Формула: (COUNT(точек с signal_level < -110) / total_points) * 100.')
    bit_hz_good_pct = mapped_column(Numeric(5, 2), comment='% времени в хорошей зоне (Bit/Hz). Формула: (COUNT(точек с bit_hz > 5) / total_points) * 100.')
    bit_hz_moderate_pct = mapped_column(Numeric(5, 2), comment='% времени в умеренной зоне (Bit/Hz). Формула: (COUNT(точек с bit_hz BETWEEN 3 AND 5) / total_points) * 100.')
    bit_hz_serious_pct = mapped_column(Numeric(5, 2), comment='% времени в серьезной зоне (Bit/Hz). Формула: (COUNT(точек с bit_hz BETWEEN 1 AND 3) / total_points) * 100.')
    bit_hz_critical_pct = mapped_column(Numeric(5, 2), comment='% времени в критической зоне (Bit/Hz). Формула: (COUNT(точек с bit_hz < 1) / total_points) * 100.')
    services_count = mapped_column(Integer, comment='Количество подключенных основных услуг за месяц (из service.activated_services)')
    services_revenue = mapped_column(Numeric(10, 2), comment='Общая сумма подключенных основных услуг за месяц в рублях (из service.activated_services)')
    clv_10_90 = mapped_column(Numeric(10, 2), comment='CLV по абонентам. Отрезаны первые и последние 10 процентов пользователей')
    clv_10_90_lifetimes = mapped_column(Numeric(10, 1), comment='Среднее время жизни абонента с отрезанием 10 процентов сверху и снизу')
    churn_amount = mapped_column(BigInteger, comment='Число абонентов, которые когда-то были на станции, но за последние 3 месяца от них на станции не было трафика')
    vno = mapped_column(Integer)
    nds_proc = mapped_column(Numeric(5, 2), comment='Процентная ставка НДС')
    fine_proc = mapped_column(Numeric(5, 2), server_default=text('0'), comment='Процент штрафа')
    fine_amount = mapped_column(Numeric(10, 2), server_default=text('0'), comment='Сумма штрафа')
    pays_count = mapped_column(BigInteger, server_default=text('0'), comment='Количество уникальных плательщиков за период')
    new_users_with_tariff = mapped_column(Integer, server_default=text('0'), comment='Сколько новых абонентов подключили тариф')
    chat_messages_count = mapped_column(BigInteger, server_default=text('0'), comment='Сколько сообщений в чате было от абонентов')
    chat_messages_unique_users = mapped_column(Integer, server_default=text('0'), comment='Число уникальных пользователей, которые обратились в чат')
    avg_signal_7d = mapped_column(Numeric(5, 2), comment='Средний сигнал за последние 7 дней')
    avg_signal_1d = mapped_column(Numeric(5, 2), comment='Средний сигнал за сутки')
    avg_bit_hz_7d = mapped_column(Numeric(5, 2), comment='Средний Бит/Гц за 7 дней')
    avg_bit_hz_1d = mapped_column(Numeric(5, 2), comment='Средний Бит/Гц за сутки')


class PricePer1Mb(Base):
    __tablename__ = 'price_per_1_mb'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90354_price_per_1mb_primary'),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger)
    channel_id = mapped_column(Integer, nullable=False)
    cost = mapped_column(Numeric(10, 2), nullable=False)


class SatelliteThresholds(Base):
    __tablename__ = 'satellite_thresholds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='satellite_thresholds_pkey'),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger)
    issue_level = mapped_column(String(50), nullable=False)
    antenna_size = mapped_column(Integer, nullable=False)
    satellite = mapped_column(Integer, comment='ID из stations.ip_group_channel')
    signal = mapped_column(Numeric(5, 2))
    bit_per_hz = mapped_column(Numeric(5, 2))


class ServiceStatPerBortMonthly(Base):
    __tablename__ = 'service_stat_per_bort_monthly'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='service_stat_per_bort_monthly_pkey'),
        Index('idx_roi_bort', 'bort'),
        Index('idx_roi_service_id', 'service_id'),
        Index('idx_roi_yearmonth', 'yearmonth'),
        Index('uq_service_stat_per_bort_monthly', 'service_id', 'yearmonth', 'bort', unique=True),
        {'schema': 'statistics'}
    )

    id = mapped_column(BigInteger)
    service_id = mapped_column(BigInteger, nullable=False)
    yearmonth = mapped_column(Integer, nullable=False)
    bort = mapped_column(Integer, nullable=False)
    traffic_mb = mapped_column(Numeric(12, 2))
    allocated_revenue_rub = mapped_column(Numeric(12, 2), comment='Сумма платежа + сумма на доп услуги, распределенная на основе потребления трафика по бортам')
    channel_cost_rub = mapped_column(Numeric(12, 2))
    profit_rub = mapped_column(Numeric(12, 2))
    profitability_percent = mapped_column(Numeric(10, 2))
    calculated_at = mapped_column(DateTime(True), server_default=text('now()'))
    cost_per_1_mb = mapped_column(Numeric(10, 2))

