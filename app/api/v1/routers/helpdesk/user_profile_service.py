"""Сбор данных и действия для карточки абонента."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request
from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.user_profile_schemas import (
    ActionMessage,
    PaymentHistoryItem,
    PaymentHistoryListResponse,
    TariffHistoryItem,
    TariffHistoryListResponse,
    ProfileHealthCheck,
    ProfileOnline,
    ProfileOpenSession,
    ProfilePersonal,
    ProfileTariffActive,
    ProfileTicket,
    ProfileTicketListResponse,
    TariffBlockResponse,
    TicketSubscriberAccountSummary,
    TicketSubscriberTariffSummary,
    UserProfileResponse,
)
from app.api.v1.routers.helpdesk.user_profile_utils import (
    bytes_to_mb,
    coalesce_int,
    PAY_STATE_LABELS,
    PAY_TYPE_LABELS,
    format_dt_msk,
    format_dop_type_label,
    format_money_ru,
    format_mb,
    format_seconds_remaining,
    format_speed_display,
    format_valid_date_countdown,
    format_valid_date_remaining,
    format_jur_active_contract,
    format_residence_address,
    format_session_duration,
    format_traffic_mb,
    jur_frozen_traffic_mb,
    jur_traffic_overrun_mb,
    parse_speed_line,
    pick_rate_limit,
    tariff_display_name,
    traffic_reset_labels,
)
from app.api.v1.routers.helpdesk.operator_log_service import write_operator_log
from app.api.v1.routers.users.dao import (
    RadacctDAO,
    ResetTrafficActionDAO,
    UserArchiveDAO,
    UserFreezeTariffDAO,
    UsersDAO,
)
from app.core.user_cache import (
    DISCONNECT_SESSIONS_MAX,
    DISCONNECT_SESSIONS_WINDOW_SEC,
    check_disconnect_sessions_allowed,
    get_disconnect_sessions_remaining,
    on_tariff_freeze_changed,
    on_unarchive,
    record_disconnect_sessions_success,
)
from app.api.v1.routers.users.subscriber_search import _format_passport
from app.constants import STATUS_DISPLAY, SUPPORT_LINE_DISPLAY
from app.models.users import TrackerTickets, User, UserDetails, UserFreezeTariff

_ENTITY = {0: "Физическое лицо", 1: "Физическое лицо", 2: "Юридическое лицо"}
_STATUS = {1: "Активен", 2: "Заморожен", 3: "В архиве"}
_FREEZE_ALREADY_USED_MSG = (
    "В рамках данного тарифа абоненту уже был заморожен тарифный план. "
    "Если абоненту требуется повторная заморозка, создайте тикет инженерам "
    "и опишите ситуацию, чтобы они приняли решение о повторной заморозке."
)
_UNFREEZE_TECH_REASON_MSG = (
    "Данный абонент был заморожен по техническим причинам. "
    "Создайте заявку инженерам, чтобы получить детали заморозки "
    "и примерные сроки разморозки тарифа абонента"
)


async def _require_juridical_subscriber(session: AsyncSession, user_id: int) -> dict[str, Any]:
    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    if int(row.get("is_juridical") or 0) != 2:
        raise HTTPException(status_code=400, detail="Действие доступно только для юридических лиц")
    return row


async def _require_physical_subscriber(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """Заморозка, разморозка и восстановление УЗ — только для is_juridical=0."""
    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    if int(row.get("is_juridical") or 0) != 0:
        raise HTTPException(
            status_code=403,
            detail="Операция доступна только для абонентов — физических лиц",
        )
    return row


async def _load_personal(session: AsyncSession, user_id: int) -> ProfilePersonal:
    personal, _balance = await _load_personal_with_balance(session, user_id)
    return personal


async def _load_active_jur_contract(session: AsyncSession, user_id: int) -> str | None:
    """Действующий договор ЮЛ: при нескольких — с наименьшим number (старший)."""
    row = (
        await session.execute(
            text("""
                SELECT
                    jcl2.first_letter,
                    jcl2."year",
                    jcl2."number",
                    jcl2.last_letter,
                    jcl2.effective_date
                FROM oss.jur_client_list jcl
                JOIN oss.jur_contract_list jcl2 ON jcl2.juridical_id = jcl.id
                JOIN users."user" u ON u.juridical_id = jcl.id
                WHERE u.id = :uid
                  AND jcl2.status = 'Действует'
                ORDER BY jcl2."number" ASC NULLS LAST
                LIMIT 1
            """),
            {"uid": user_id},
        )
    ).mappings().one_or_none()
    return format_jur_active_contract(dict(row) if row else None)


async def _load_personal_with_balance(
    session: AsyncSession, user_id: int
) -> tuple[ProfilePersonal, float]:
    """Один запрос: user + LATERAL user_details + станция (без оконной функции по всей user_details)."""
    row = (
        await session.execute(
            text("""
                SELECT
                    u.id,
                    u.login,
                    u.email,
                    u.mob_tel,
                    u.is_juridical,
                    u.user_status,
                    u.full_name,
                    u.passport,
                    u.balanse,
                    ud.surname AS ud_surname,
                    ud.name AS ud_name,
                    ud.patronymic AS ud_patronymic,
                    ud.pas_series AS ud_pas_series,
                    ud.pas_number AS ud_pas_number,
                    ud.address AS ud_address,
                    ud.city AS ud_city,
                    ud.street AS ud_street,
                    ud.house AS ud_house,
                    ud.flat AS ud_flat,
                    jcl.short_name_organization,
                    jcl.email_organization,
                    jcl.phone_organization,
                    jcl.inn,
                    jcl.city AS jur_city,
                    jcl.street AS jur_street,
                    jcl.house AS jur_house,
                    jcl.addr_organization,
                    coalesce(sf.station_name, ig.name) AS station_name,
                    h.ip AS auth_page
                FROM users."user" u
                LEFT JOIN LATERAL (
                    SELECT ud.surname, ud.name, ud.patronymic, ud.pas_series, ud.pas_number,
                        ud.address, ud.city, ud.street, ud.house, ud.flat
                    FROM users.user_details ud
                    WHERE ud.user_id = u.id
                    ORDER BY ud.is_actual DESC NULLS LAST, ud.id DESC
                    LIMIT 1
                ) ud ON true
                LEFT JOIN oss.jur_client_list jcl ON jcl.id = u.juridical_id
                LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp
                LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
                LEFT JOIN stations.hotspot h ON h.id = ig.id_hotspot
                WHERE u.id = :uid
            """),
            {"uid": user_id},
        )
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Абонент не найден")

    is_jur = int(row["is_juridical"] or 0)
    active_contract: str | None = None
    residence_address: str | None = None
    if is_jur == 2:
        name = (row["short_name_organization"] or row["full_name"] or "").strip()
        email = row["email_organization"]
        phone = row["phone_organization"]
        id_doc = (row["inn"] or "").strip() or None
        contract_label = await _load_active_jur_contract(session, user_id)
        active_contract = contract_label or "Не удалось найти договор"
        residence_address = format_residence_address(
            2,
            city=row.get("jur_city"),
            street=row.get("jur_street"),
            house=row.get("jur_house"),
            addr_organization=row.get("addr_organization"),
        )
    else:
        parts = [row["ud_surname"], row["ud_name"], row["ud_patronymic"]]
        name = " ".join(p for p in parts if p and str(p).strip()).strip() or (row["full_name"] or "")
        email = row["email"]
        phone = row["mob_tel"]
        id_doc = _format_passport(row["ud_pas_series"], row["ud_pas_number"], None)
        residence_address = format_residence_address(
            0,
            address=row.get("ud_address"),
            city=row.get("ud_city"),
            street=row.get("ud_street"),
            house=row.get("ud_house"),
            flat=row.get("ud_flat"),
        )

    us = int(row["user_status"]) if row["user_status"] is not None else 1
    personal = ProfilePersonal(
        user_id=int(row["id"]),
        name=name or f"#{row['id']}",
        login=(row["login"] or "").strip(),
        email=(email or "").strip() or None,
        phone=(phone or "").strip() or None,
        id_doc=id_doc,
        active_contract=active_contract,
        is_juridical=is_jur,
        entity_label=_ENTITY.get(is_jur, "Физическое лицо"),
        user_status=us,
        status_label=_STATUS.get(us, "Неизвестно"),
        station_name=row["station_name"],
        auth_page=row["auth_page"],
        residence_address=residence_address,
    )
    return personal, float(row["balanse"] or 0)


def _online_from_radacct_summary(
    is_online: bool, last_end: Optional[datetime]
) -> ProfileOnline:
    return ProfileOnline(
        is_online=is_online,
        last_session_end=last_end,
        last_session_end_label=format_dt_msk(last_end) if last_end else None,
    )


def _freeze_reason_code(freeze: Optional[dict[str, Any]]) -> int:
    if not freeze:
        return 0
    code = freeze.get("reason_code")
    if code is None:
        raw = freeze.get("reason")
        if raw is not None and str(raw).strip().isdigit():
            code = int(str(raw).strip())
    return int(code or 0)


def _was_tariff_frozen_before(trow: Optional[dict[str, Any]]) -> bool:
    return int((trow or {}).get("was_frozen") or 0) == 1


async def _assert_physical_can_freeze(session: AsyncSession, user_id: int) -> None:
    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    login = (row.get("login") or "").strip()
    if not login:
        raise HTTPException(status_code=400, detail="У абонента не задан логин")
    trow = await _load_tariff_row(session, user_id, login)
    if _was_tariff_frozen_before(trow):
        raise HTTPException(status_code=400, detail=_FREEZE_ALREADY_USED_MSG)


async def _assert_physical_can_unfreeze(session: AsyncSession, user_id: int) -> None:
    freeze = await _load_freeze(session, user_id)
    if not freeze or not freeze.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Тариф не заморожен")
    if _freeze_reason_code(freeze) == 4:
        raise HTTPException(status_code=400, detail=_UNFREEZE_TECH_REASON_MSG)


async def _load_tariff_row(session: AsyncSession, user_id: int, login: str) -> Optional[dict[str, Any]]:
    r = await session.execute(
        text("""
            SELECT u.id,
                CASE WHEN u.is_juridical = 0 THEN s.name ELSE
                    CASE WHEN s.real_type = 'default' THEN 'Лимитный тариф'
                         ELSE 'Безлимитный тариф' END
                END AS tariff_name,
                s.real_type,
                sg.rate,
                sg.u_slow_rate,
                CASE WHEN s.real_type = 'default' THEN r3.remain_val
                     ELSE ru.now_day_traffic END AS remain_traffic,
                CASE WHEN s.real_type = 'default' THEN r3.full_val
                     ELSE ru.full_packet END AS full_packet,
                CASE WHEN s.real_type = 'unlim_fap' OR u.is_juridical = 0 THEN NULL
                     ELSE sj.normal_traffic END AS jur_normal_traffic,
                CASE
                    WHEN r.groupname IS NULL THEN 0
                    WHEN r.groupname = 'disabled' THEN 0
                    ELSE 1
                END AS is_active,
                r.groupname AS rad_groupname,
                r.sname AS rad_sname,
                r.was_frozen,
                usd.traffic_renew_count,
                usd.valid_date,
                u.traffic_update_hour AS msk_hour,
                ig.gmt,
                ru.now_day_traffic AS unlim_day_traffic
            FROM users."user" u
            LEFT JOIN LATERAL (
                SELECT r.groupname, r.sname, r.priority, r.was_frozen
                FROM radius.radusergroup r
                WHERE lower(r.username) = lower(u.login)
                ORDER BY r.priority NULLS LAST
                LIMIT 1
            ) r ON true
            LEFT JOIN service.service s ON s.sname = r.sname
            LEFT JOIN radius.radgroupreply r2 ON r2.groupname = s.sname
                AND r2.attribute = 'Mikrotik-Rate-Limit'
            LEFT JOIN service.service_groups sg ON sg.id = r2.fap_id
            LEFT JOIN LATERAL (
                SELECT NULLIF(trim(rr.value), '')::bigint AS remain_val,
                    NULLIF(trim(rr.full_packet), '')::bigint AS full_val
                FROM radius.radreply rr
                WHERE lower(rr.username) = lower(u.login)
                ORDER BY rr.id DESC
                LIMIT 1
            ) r3 ON true
            LEFT JOIN radius.radreply_unlim ru ON ru.uid = u.id
            LEFT JOIN service.service_jur sj ON sj.service = s.sname
            LEFT JOIN users.user_service_date usd ON usd.user_id = u.id
            LEFT JOIN wifitochka.ip_group ig ON ig.id = u.id_grp
            WHERE u.id = :uid
        """),
        {"uid": user_id},
    )
    row = r.mappings().one_or_none()
    return dict(row) if row else None


async def _load_freeze(session: AsyncSession, user_id: int) -> Optional[dict[str, Any]]:
    return await UserFreezeTariffDAO.find_one_with_reason(session, user_id)


async def _load_service_by_sname(session: AsyncSession, sname: str) -> Optional[dict[str, Any]]:
    r = await session.execute(
        text("SELECT name, real_type::text AS real_type FROM service.service WHERE sname = :sn LIMIT 1"),
        {"sn": sname},
    )
    row = r.mappings().one_or_none()
    return dict(row) if row else None


async def _load_jur_normal_traffic(session: AsyncSession, sname: str) -> Optional[int]:
    r = await session.execute(
        text("SELECT normal_traffic FROM service.service_jur WHERE service = :sn LIMIT 1"),
        {"sn": sname},
    )
    val = r.scalar_one_or_none()
    return int(val) if val is not None else None


async def _load_netflow(session: AsyncSession, user_id: int) -> tuple[Optional[str], Optional[str]]:
    r = await session.execute(
        text("""
            SELECT sjbm.sname
            FROM users.netflow_users nu
            LEFT JOIN service.service_jur_by_months sjbm ON sjbm.user_id = nu.uid
            WHERE nu.uid = :uid
              AND sjbm.year = extract(year FROM now())
              AND sjbm.month = extract(month FROM now())
            LIMIT 1
        """),
        {"uid": user_id},
    )
    sname = r.scalar_one_or_none()
    if not sname:
        return None, None
    return "Работа через индивидуальную станцию (Netflow).", str(sname)


def _has_radusergroup(trow: Optional[dict[str, Any]]) -> bool:
    """Есть запись в radius.radusergroup (как в fast_check_service._is_tariff_connected)."""
    return bool(((trow or {}).get("rad_groupname") or "").strip())


def _is_limited_tariff_ended(trow: Optional[dict[str, Any]]) -> bool:
    """Лимитный тариф: groupname=disabled в radusergroup — пакет исчерпан, услуга ещё до valid_date."""
    if not trow:
        return False
    gn = ((trow.get("rad_groupname") or "").strip().lower())
    return (trow.get("real_type") or "").strip() == "default" and gn == "disabled"


def _last_traffic_reset_label(ts: Optional[datetime]) -> str:
    return format_dt_msk(ts) if ts else "Еще не было"


def _build_tariff(
    trow: Optional[dict[str, Any]],
    freeze: Optional[dict[str, Any]],
    is_jur: int,
    *,
    service_meta: Optional[dict[str, Any]] = None,
    jur_normal: Optional[int] = None,
    last_script_reset_at: Optional[datetime] = None,
) -> Optional[ProfileTariffActive]:
    is_fl = is_jur == 0

    if freeze and freeze.get("is_frozen"):
        remain = coalesce_int(freeze.get("remaining_traffic"))
        full = coalesce_int(freeze.get("full_packet"))
        sname = freeze.get("tariff")
        name = tariff_display_name(is_jur, service_meta, sname)
        jur_main_remain: Optional[float] = None
        jur_dop_used: Optional[float] = None
        overrun: Optional[float] = None
        if is_jur == 2 and jur_normal is not None and full:
            jur_main_remain, jur_dop_used = jur_frozen_traffic_mb(remain, full, jur_normal)
            overrun = jur_dop_used
        tech_freeze = is_fl and _freeze_reason_code(freeze) == 4
        return ProfileTariffActive(
            state="frozen",
            tariff_name=name,
            real_type=(service_meta or {}).get("real_type"),
            is_active=False,
            remain_traffic_mb=bytes_to_mb(remain),
            full_packet_mb=bytes_to_mb(full),
            jur_main_packet_mb=jur_main_remain,
            jur_dop_packet_mb=None,
            overrun_mb=overrun,
            frozen_at=format_dt_msk(freeze.get("date_freeze")),
            unfreeze_at=format_dt_msk(freeze.get("date_unfreeze")),
            frozen_remaining_label=format_seconds_remaining(freeze.get("remaining_time")),
            freeze_reason=freeze.get("reason_short") or freeze.get("reason"),
            unfreeze_blocked_message=_UNFREEZE_TECH_REASON_MSG if tech_freeze else None,
            can_unfreeze=is_fl and not tech_freeze,
            can_freeze=False,
            can_cancel_planned_freeze=False,
            can_remove_ended_tariff=False,
            can_disconnect_sessions=is_jur == 2,
        )

    if not _has_radusergroup(trow):
        return None

    planned = bool(freeze and not freeze.get("is_frozen"))
    real_type = (trow or {}).get("real_type")
    is_active = bool((trow or {}).get("is_active", 0))
    rate_raw = pick_rate_limit(
        (trow or {}).get("rate"),
        (trow or {}).get("u_slow_rate"),
        (trow or {}).get("unlim_day_traffic"),
    )
    up, down = parse_speed_line(rate_raw)
    remain = coalesce_int(
        (trow or {}).get("remain_traffic"),
        freeze.get("remaining_traffic") if freeze else None,
    )
    full = coalesce_int(
        (trow or {}).get("full_packet"),
        freeze.get("full_packet") if freeze else None,
    )
    valid_date = (trow or {}).get("valid_date")
    disconnect_label = format_valid_date_countdown(valid_date)
    jur_n = (trow or {}).get("jur_normal_traffic")
    overrun = None
    jur_main_mb = None
    jur_dop_mb = None
    if is_jur == 2 and jur_n and full:
        jur_main_mb = bytes_to_mb(jur_n)
        jur_dop_mb = bytes_to_mb(int(full) - int(jur_n))
        overrun = jur_traffic_overrun_mb(remain, full, jur_n)

    msk_reset = local_reset = None
    renew = None
    if real_type == "unlim_fap" and trow:
        msk_reset, local_reset = traffic_reset_labels(trow.get("msk_hour"), trow.get("gmt"))
        renew = trow.get("traffic_renew_count")

    tariff_ended = _is_limited_tariff_ended(trow)
    if tariff_ended:
        state = "ended"
        is_active = False
    elif planned:
        state = "planned_freeze"
    elif is_active:
        state = "active"
    else:
        state = "inactive"

    remain_mb = bytes_to_mb(remain)
    full_mb = bytes_to_mb(full)
    if tariff_ended:
        remain_mb = 0.0

    was_frozen_before = _was_tariff_frozen_before(trow)
    freeze_allowed = is_fl and is_active and not planned and not was_frozen_before

    return ProfileTariffActive(
        state=state,
        tariff_name=(trow or {}).get("tariff_name") or (freeze.get("tariff") if freeze else "—"),
        real_type=real_type,
        is_active=is_active,
        rate_up=format_speed_display(up),
        rate_down=format_speed_display(down),
        speed_unlimited=real_type == "unlim_fap",
        remain_traffic_mb=remain_mb,
        full_packet_mb=full_mb,
        disconnect_at_label=disconnect_label,
        valid_date_label=format_dt_msk(valid_date),
        remaining_label=format_valid_date_remaining(valid_date),
        jur_main_packet_mb=jur_main_mb,
        jur_dop_packet_mb=jur_dop_mb,
        overrun_mb=overrun,
        traffic_renew_count=renew,
        msk_reset=msk_reset,
        local_reset=local_reset,
        last_traffic_reset_label=(
            _last_traffic_reset_label(last_script_reset_at)
            if real_type == "unlim_fap"
            else None
        ),
        planned_freeze_at=format_dt_msk(freeze.get("date_freeze")) if planned else None,
        unfreeze_at=format_dt_msk(freeze.get("date_unfreeze")) if planned else None,
        freeze_blocked_message=(
            _FREEZE_ALREADY_USED_MSG
            if is_fl and is_active and not planned and was_frozen_before
            else None
        ),
        can_freeze=freeze_allowed,
        can_unfreeze=False,
        can_cancel_planned_freeze=is_fl and planned,
        can_remove_ended_tariff=is_fl and tariff_ended,
        can_disconnect_sessions=True,
    )


_TICKETS_BASE_WHERE = "tt.user_id = :uid"

_PROFILE_TARIFFS_LIMIT = 10
_PROFILE_PAYMENTS_SUCCESS_LIMIT = 10

_TICKETS_SELECT = """
    SELECT tt.id, tt.title, tc.name AS category_name, tc.theme::text AS category_theme,
        tt.date_of_create, tt.date_of_close,
        CASE
            WHEN su.role = 'engineer' THEN 'Инженеры'
            WHEN su.role = 'manager' THEN 'Менеджер'
            WHEN su.role = 'support' THEN 'Контактный центр'
            ELSE NULL
        END AS assigned_to_role,
        tt.support_line, tt.status::text AS status
    FROM users.tracker_tickets tt
    LEFT JOIN users.ticket_categories tc ON tc.id = tt.category_id
    LEFT JOIN users.skystream_users su ON su.id = tt.assigned_to
    WHERE """ + _TICKETS_BASE_WHERE + """
    ORDER BY tt.date_of_create DESC
    LIMIT :limit OFFSET :offset
"""

_PAYMENTS_FILTERED = """
    WITH dated AS (
        SELECT
            p.id,
            COALESCE(
                CASE WHEN p.date_in > 0
                    THEN timezone('Europe/Moscow', to_timestamp(p.date_in))
                    ELSE NULL
                END,
                p.date_in_tz
            ) AS msk_date,
            p.state::text AS state,
            p.type AS payment_type,
            p.amount AS amount
        FROM payments.pays p
        WHERE p.uid = :uid
    ),
    payed_top AS (
        SELECT id, msk_date,
            ROW_NUMBER() OVER (ORDER BY msk_date DESC NULLS LAST) AS payed_rn
        FROM dated
        WHERE state = 'payed'
    ),
    bounds AS (
        SELECT
            MIN(msk_date) FILTER (WHERE payed_rn <= :payed_limit) AS t_min,
            MAX(msk_date) FILTER (WHERE payed_rn <= :payed_limit) AS t_max
        FROM payed_top
    ),
    filtered AS (
        SELECT d.msk_date, d.state, d.payment_type, d.amount
        FROM dated d
        CROSS JOIN bounds b
        WHERE (
            d.state = 'payed'
            AND d.id IN (SELECT id FROM payed_top WHERE payed_rn <= :payed_limit)
        )
        OR (
            d.state <> 'payed'
            AND b.t_min IS NOT NULL
            AND b.t_max IS NOT NULL
            AND d.msk_date >= b.t_min
            AND d.msk_date <= b.t_max
        )
    )
"""

_PAYMENTS_COUNT = _PAYMENTS_FILTERED + " SELECT count(*)::int FROM filtered"

_PAYMENTS_PAGE = _PAYMENTS_FILTERED + """
    SELECT msk_date, state, payment_type, amount
    FROM filtered
    ORDER BY msk_date DESC NULLS LAST
    LIMIT :limit OFFSET :offset
"""

_JUR_PAYMENTS_COUNT = """
    SELECT count(*)::int
    FROM payments.pays_bills pb
    WHERE pb.system = 'contract'
      AND pb.id_user = :uid
"""

_JUR_PAYMENTS_PAGE = """
    SELECT
        pb.amount,
        COALESCE(
            CASE WHEN pb.date > 0
                THEN timezone('Europe/Moscow', to_timestamp(pb.date))
                ELSE NULL
            END,
            timezone('Europe/Moscow', pb.datum)
        ) AS msk_date,
        'rs' AS payment_type,
        'payed' AS state
    FROM payments.pays_bills pb
    WHERE pb.system = 'contract'
      AND pb.id_user = :uid
    ORDER BY pb.datum DESC
    LIMIT :limit OFFSET :offset
"""

_TARIFF_HISTORY_FILTERED = """
    WITH ranked_tariffs AS (
        SELECT
            t.activation_timestamp,
            t.deactivation_date,
            t.packet_size,
            t.days,
            t.price,
            t.sname,
            s.real_type::text AS real_type,
            ROW_NUMBER() OVER (ORDER BY t.activation_timestamp DESC) AS rn_desc,
            LEAD(t.activation_timestamp) OVER (ORDER BY t.activation_timestamp ASC) AS next_activation
        FROM service.activated_services t
        LEFT JOIN service.service s ON s.sname = t.sname
        WHERE t.uid = :uid
    ),
    top_tariffs AS (
        SELECT *,
            COALESCE(deactivation_date, next_activation, now()) AS period_end
        FROM ranked_tariffs
        WHERE rn_desc <= :tariff_limit
    ),
    tariff_rows AS (
        SELECT
            activation_timestamp AS activated_at,
            'tariff'::text AS row_kind,
            real_type,
            deactivation_date,
            packet_size,
            days,
            price,
            NULL::text AS dop_name,
            sname
        FROM top_tariffs
    ),
    dop_rows AS (
        SELECT
            ad.activation_timestamp::timestamptz AS activated_at,
            'dop'::text AS row_kind,
            NULL::text AS real_type,
            NULL::timestamptz AS deactivation_date,
            NULL::bigint AS packet_size,
            NULL::int AS days,
            ad.price,
            ad.dop_name,
            NULL::text AS sname
        FROM service.activated_dops ad
        WHERE ad.uid = :uid
          AND EXISTS (
              SELECT 1
              FROM top_tariffs tt
              WHERE ad.activation_timestamp::timestamptz >= tt.activation_timestamp
                AND ad.activation_timestamp::timestamptz < tt.period_end
          )
    ),
    filtered AS (
        SELECT * FROM tariff_rows
        UNION ALL
        SELECT * FROM dop_rows
    )
"""

_TARIFF_HISTORY_COUNT = _TARIFF_HISTORY_FILTERED + " SELECT count(*)::int FROM filtered"

_TARIFF_HISTORY_PAGE = _TARIFF_HISTORY_FILTERED + """
    SELECT * FROM filtered
    ORDER BY activated_at DESC NULLS LAST
    LIMIT :limit OFFSET :offset
"""


def _row_to_profile_ticket(row: Any) -> ProfileTicket:
    st = row["status"] or "open"
    line = int(row["support_line"] or 1)
    return ProfileTicket(
        id=int(row["id"]),
        title=row["title"] or f"Тикет #{row['id']}",
        category=row["category_name"],
        category_theme=row["category_theme"],
        date_of_create=row["date_of_create"],
        date_of_close=row["date_of_close"],
        assigned_to_role=row["assigned_to_role"],
        support_line=line,
        support_line_label=SUPPORT_LINE_DISPLAY.get(line, str(line)),
        status=st,
        status_label=STATUS_DISPLAY.get(st, st),
    )


async def load_user_tickets_page(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
) -> ProfileTicketListResponse:
    total = int(
        (
            await session.execute(
                text(
                    f"""
                    SELECT count(*)::int
                    FROM users.tracker_tickets tt
                    WHERE {_TICKETS_BASE_WHERE}
                    """
                ),
                {"uid": user_id},
            )
        ).scalar_one()
        or 0
    )
    offset = (page - 1) * per_page
    r = await session.execute(
        text(_TICKETS_SELECT),
        {"uid": user_id, "limit": per_page, "offset": offset},
    )
    items = [_row_to_profile_ticket(row) for row in r.mappings().all()]
    return ProfileTicketListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )


def _row_to_payment_item(row: Any) -> PaymentHistoryItem:
    msk = row["msk_date"]
    if msk is not None and msk.tzinfo is None:
        msk = msk.replace(tzinfo=timezone.utc)
    state = str(row["state"] or "in")
    pay_type = str(row["payment_type"] or "")
    amount = float(row["amount"] or 0)
    return PaymentHistoryItem(
        msk_date=msk,
        msk_date_label=format_dt_msk(msk, time_sep=" ") or "—",
        state=state,
        state_label=PAY_STATE_LABELS.get(state, state),
        payment_type=pay_type,
        type_label=PAY_TYPE_LABELS.get(pay_type, pay_type or "—"),
        amount=amount,
    )


async def load_user_payments_page(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
) -> PaymentHistoryListResponse:
    is_jur = (
        await session.execute(
            text('SELECT is_juridical FROM users."user" WHERE id = :uid'),
            {"uid": user_id},
        )
    ).scalar_one_or_none()
    if is_jur is None:
        raise HTTPException(status_code=404, detail="Абонент не найден")

    offset = (page - 1) * per_page
    if int(is_jur or 0) == 2:
        total = int(
            (await session.execute(text(_JUR_PAYMENTS_COUNT), {"uid": user_id})).scalar_one() or 0
        )
        r = await session.execute(
            text(_JUR_PAYMENTS_PAGE),
            {"uid": user_id, "limit": per_page, "offset": offset},
        )
    else:
        params = {"uid": user_id, "payed_limit": _PROFILE_PAYMENTS_SUCCESS_LIMIT}
        total = int(
            (await session.execute(text(_PAYMENTS_COUNT), params)).scalar_one() or 0
        )
        r = await session.execute(
            text(_PAYMENTS_PAGE),
            {**params, "limit": per_page, "offset": offset},
        )

    items = [_row_to_payment_item(row) for row in r.mappings().all()]
    return PaymentHistoryListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )


async def load_user_tariff_history_page(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
) -> TariffHistoryListResponse:
    params = {"uid": user_id, "tariff_limit": _PROFILE_TARIFFS_LIMIT}
    total = int(
        (await session.execute(text(_TARIFF_HISTORY_COUNT), params)).scalar_one() or 0
    )
    offset = (page - 1) * per_page
    r = await session.execute(
        text(_TARIFF_HISTORY_PAGE),
        {**params, "limit": per_page, "offset": offset},
    )
    items = [_row_to_tariff_history_item(row) for row in r.mappings().all()]
    return TariffHistoryListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )


def _tariff_type_label(real_type: Optional[str]) -> str:
    if real_type == "default" or not real_type:
        return "Лимитный"
    return "Безлимитный"


def _row_to_tariff_history_item(row: Any) -> TariffHistoryItem:
    activated = row["activated_at"]
    if activated is not None and activated.tzinfo is None:
        activated = activated.replace(tzinfo=timezone.utc)
    kind = row["row_kind"]
    price_val = row.get("price")
    price = float(price_val) if price_val is not None else None
    deact = row.get("deactivation_date")
    if deact is not None and hasattr(deact, "tzinfo") and deact.tzinfo is None:
        deact = deact.replace(tzinfo=timezone.utc)
    if kind == "dop":
        type_label, type_hint = format_dop_type_label(row.get("dop_name"))
        active_tariff = False
        deact_label = "—"
    else:
        type_label = _tariff_type_label(row.get("real_type"))
        type_hint = None
        active_tariff = deact is None
        deact_label = (
            "Активный тариф"
            if active_tariff
            else (format_dt_msk(deact, time_sep=" ", short_year=True) or "—")
        )

    return TariffHistoryItem(
        activated_at=activated,
        activated_at_label=format_dt_msk(activated, time_sep=" ", short_year=True) or "—",
        row_kind=kind,
        type_label=type_label,
        type_hint=type_hint,
        active_tariff=active_tariff,
        deactivation_at_label=deact_label,
        price=price,
        price_label=format_money_ru(price),
    )


def _build_health_check(personal: ProfilePersonal, online: ProfileOnline, tariff: Optional[ProfileTariffActive], balance: float) -> ProfileHealthCheck:
    items: list[str] = []
    if personal.user_status == 3:
        items.append("Учётная запись в архиве — восстановите УЗ или уточните причину обращения.")
    if balance < 0:
        items.append(f"Отрицательный баланс ({balance:.2f} ₽) — возможны ограничения услуг.")
    elif balance == 0:
        items.append("Нулевой баланс — рекомендуется проверить последние платежи.")
    if tariff:
        if tariff.state == "frozen":
            items.append("Тариф заморожен — услуги приостановлены.")
        elif tariff.state == "planned_freeze":
            items.append(f"Запланирована заморозка: {tariff.planned_freeze_at}.")
        elif not tariff.is_active:
            items.append("Тариф неактивен — абонент не сможет авторизоваться.")
        elif tariff.overrun_mb:
            items.append(f"Перерасход трафика: ~{tariff.overrun_mb:.1f} МБ сверх основного пакета.")
    if not online.is_online and online.last_session_end_label:
        items.append(f"Абонент офлайн. Последняя сессия: {online.last_session_end_label}.")
    elif online.is_online:
        items.append("Абонент в сети — сессия активна.")
    if not items:
        items.append("Критичных отклонений не обнаружено. Детали — в блоке тарифа и истории.")
    return ProfileHealthCheck(items=items)


async def _load_tariff_bundle(
    session: AsyncSession,
    user_id: int,
    personal: ProfilePersonal,
) -> tuple[Optional[ProfileTariffActive], Optional[str], Optional[str]]:
    trow, freeze, netflow_pair = await asyncio.gather(
        _load_tariff_row(session, user_id, personal.login),
        _load_freeze(session, user_id),
        _load_netflow(session, user_id),
    )
    netflow_note, netflow_tariff = netflow_pair
    freeze_sname = (freeze or {}).get("tariff") if freeze else None
    service_meta = await _load_service_by_sname(session, freeze_sname) if freeze_sname else None
    if service_meta is None and trow and trow.get("real_type"):
        service_meta = {"name": trow.get("tariff_name"), "real_type": trow.get("real_type")}
    jur_normal = None
    if freeze_sname and personal.is_juridical == 2:
        jur_normal = await _load_jur_normal_traffic(session, freeze_sname)
    last_script_reset_at: Optional[datetime] = None
    if trow and (trow.get("real_type") or "").strip() == "unlim_fap":
        last_script_reset_at = await ResetTrafficActionDAO.find_last_script_reset_at(
            session, user_id
        )
    tariff = _build_tariff(
        trow,
        freeze,
        personal.is_juridical,
        service_meta=service_meta,
        jur_normal=jur_normal,
        last_script_reset_at=last_script_reset_at,
    )
    return tariff, netflow_note, netflow_tariff


def _profile_tariff_to_ticket_summary(
    tariff: Optional[ProfileTariffActive],
) -> TicketSubscriberTariffSummary:
    if not tariff:
        return TicketSubscriberTariffSummary(
            connected=False,
            state="none",
            status_label="Нет активного тарифа",
        )

    state = tariff.state
    if state == "frozen":
        status_label = "Заморожен"
    elif state == "planned_freeze":
        status_label = "Запланирована заморозка"
    elif state == "ended":
        status_label = "Тариф закончился"
    elif tariff.is_active:
        status_label = "Активен"
    else:
        status_label = "Неактивен"
        state = "inactive"

    type_label = "Безлимитный" if tariff.speed_unlimited else "Лимитный"
    rate_up = tariff.rate_up if tariff.rate_up and tariff.rate_up != "—" else None
    rate_down = tariff.rate_down if tariff.rate_down and tariff.rate_down != "—" else None

    return TicketSubscriberTariffSummary(
        connected=True,
        state=state,
        tariff_name=tariff.tariff_name,
        status_label=status_label,
        type_label=type_label,
        frozen_at_label=tariff.frozen_at,
        unfreeze_at_label=tariff.unfreeze_at,
        frozen_remaining_label=tariff.frozen_remaining_label,
        remain_traffic_mb=tariff.remain_traffic_mb,
        full_packet_mb=tariff.full_packet_mb,
        jur_main_packet_mb=tariff.jur_main_packet_mb,
        jur_dop_packet_mb=tariff.jur_dop_packet_mb,
        overrun_mb=tariff.overrun_mb,
        rate_up=rate_up,
        rate_down=rate_down,
        msk_reset=tariff.msk_reset,
        local_reset=tariff.local_reset,
        valid_date_label=tariff.valid_date_label,
        remaining_label=tariff.remaining_label,
    )


async def load_subscriber_account_summary(
    session: AsyncSession,
    user_id: int,
) -> TicketSubscriberAccountSummary:
    """Баланс и краткая информация о тарифе для сайдбара тикета."""
    personal, balance = await _load_personal_with_balance(session, user_id)
    tariff, _, _ = await _load_tariff_bundle(session, user_id, personal)
    return TicketSubscriberAccountSummary(
        balance=float(balance),
        tariff=_profile_tariff_to_ticket_summary(tariff),
    )


async def _assemble_tariff_block(
    session: AsyncSession,
    user_id: int,
    *,
    personal: Optional[ProfilePersonal] = None,
    balance: Optional[float] = None,
    online: Optional[ProfileOnline] = None,
) -> tuple[
    Optional[ProfileTariffActive],
    Optional[str],
    Optional[str],
    ProfileHealthCheck,
    ProfilePersonal,
    float,
    ProfileOnline,
]:
    personal, balance_loaded = await _load_personal_with_balance(session, user_id)
    if balance is None:
        balance = balance_loaded
    is_online, open_count, last_end = await RadacctDAO.get_session_summary(session, personal.login)
    online = online or _online_from_radacct_summary(is_online, last_end)
    tariff, netflow_note, netflow_tariff = await _load_tariff_bundle(session, user_id, personal)
    health = _build_health_check(personal, online, tariff, balance)
    return tariff, netflow_note, netflow_tariff, health, personal, balance, online


async def get_user_profile(
    session: AsyncSession,
    user_id: int,
    tickets_page: int = 1,
    tickets_per_page: int = 10,
    *,
    include_tickets: bool = True,
) -> UserProfileResponse:
    personal, balance = await _load_personal_with_balance(session, user_id)

    is_online, open_sessions, last_end = await RadacctDAO.get_session_summary(
        session, personal.login
    )
    open_session_items = await load_open_sessions(session, personal.login)

    if include_tickets and tickets_per_page > 0:
        tariff_res, tickets = await asyncio.gather(
            _load_tariff_bundle(session, user_id, personal),
            load_user_tickets_page(session, user_id, tickets_page, tickets_per_page),
        )
    else:
        tariff_res = await _load_tariff_bundle(session, user_id, personal)
        tickets = ProfileTicketListResponse(total=0, page=1, per_page=1, items=[])

    online = _online_from_radacct_summary(is_online, last_end)
    tariff, netflow_note, netflow_tariff = tariff_res
    health = _build_health_check(personal, online, tariff, balance)
    _, disconnect_remaining = await get_disconnect_sessions_remaining(user_id)
    if tariff is not None and disconnect_remaining <= 0:
        tariff = tariff.model_copy(update={"can_disconnect_sessions": False})

    return UserProfileResponse(
        personal=personal,
        online=online,
        open_sessions_count=open_sessions,
        open_sessions=open_session_items,
        balance=balance,
        tariff=tariff,
        netflow_note=netflow_note,
        netflow_tariff=netflow_tariff,
        health_check=health,
        tickets=tickets,
        disconnect_sessions_remaining=disconnect_remaining,
        disconnect_sessions_limit=DISCONNECT_SESSIONS_MAX,
        disconnect_sessions_window_minutes=max(1, DISCONNECT_SESSIONS_WINDOW_SEC // 60),
    )


async def remove_ended_tariff(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> TariffBlockResponse:
    """Отключение завершённого тарифа (radius.remove_user) — только для ФЛ."""
    await _require_physical_subscriber(session, user_id)
    row = await UsersDAO.find_one_or_none(session, id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    login = (row.get("login") or "").strip()
    if not login:
        raise HTTPException(status_code=400, detail="У абонента не задан логин")

    trow = await _load_tariff_row(session, user_id, login)
    if not trow:
        raise HTTPException(status_code=400, detail="Данные тарифа не найдены")
    if int(trow.get("is_active") or 0) == 1:
        raise HTTPException(
            status_code=400,
            detail="Тариф ещё активен — отключение не требуется",
        )

    f_type = str(trow.get("real_type") or "default")
    await _log_tariff_action(
        session,
        operator=operator,
        request=request,
        user_id=user_id,
        action="tariff.remove_ended",
        details={
            "login": login,
            "f_type": f_type,
            "is_juridical": int(row.get("is_juridical") or 0),
        },
    )
    await _call_radius_proc(
        session,
        "CALL radius.remove_user(:login, :ftype)",
        {"login": login, "ftype": f_type},
    )
    await session.commit()
    await on_tariff_freeze_changed(session, user_id)

    tariff, netflow_note, netflow_tariff, health, _, _, _ = await _assemble_tariff_block(
        session, user_id
    )
    return TariffBlockResponse(
        message="Тариф отключён",
        tariff=tariff,
        netflow_note=netflow_note,
        netflow_tariff=netflow_tariff,
        health_check=health,
    )


async def unarchive_user(session: AsyncSession, user_id: int) -> ActionMessage:
    row = await _require_physical_subscriber(session, user_id)
    if int(row.get("user_status") or 0) != 3 and int(row.get("archive") or 0) != 1:
        raise HTTPException(status_code=400, detail="Учётная запись не в архиве")

    n = await UsersDAO.update(
        session,
        filter_by={"id": user_id},
        user_status=1,
        archive=0,
        auto_commit=False,
    )
    if not n:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    await UserArchiveDAO.delete(session, auto_commit=False, user_id=user_id)
    await session.commit()
    await on_unarchive(session, user_id)
    return ActionMessage(message="Учётная запись восстановлена")


async def count_open_sessions(session: AsyncSession, login: str) -> int:
    _online, open_count, _last = await RadacctDAO.get_session_summary(session, login)
    return open_count


_OPEN_SESSIONS_SQL = """
    SELECT
        r.acctstarttime,
        CASE
            WHEN r.framedprotocol = 'PPP' THEN 'PPPoE'
            ELSE 'Hotspot'
        END AS protocol,
        host(r.framedipaddress)::text AS ip_address,
        st.station_name,
        coalesce(r.acctinputoctets, 0)::float / 1048576 AS traffic_in_mb,
        coalesce(r.acctoutputoctets, 0)::float / 1048576 AS traffic_out_mb
    FROM radius.radacct r
    LEFT JOIN LATERAL (
        SELECT coalesce(sf.station_name, ig.name) AS station_name
        FROM wifitochka.ip_group ig
        LEFT JOIN stations.station_forms sf ON sf.station_id = ig.id
        WHERE ig.network_hotspot >> r.framedipaddress
           OR ig.network_pppoe >> r.framedipaddress
        ORDER BY ig.id
        LIMIT 1
    ) st ON true
    WHERE lower(r.username) = lower(:login)
      AND r.acctstoptime IS NULL
    ORDER BY r.acctstarttime DESC
"""


def _row_to_open_session(row: Any, *, now: datetime) -> ProfileOpenSession:
    started = row["acctstarttime"]
    if started is not None and started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    protocol = str(row["protocol"] or "Hotspot")
    if protocol not in ("PPPoE", "Hotspot"):
        protocol = "Hotspot"
    duration_sec = 0
    if started is not None:
        duration_sec = max(0, int((now - started.astimezone(timezone.utc)).total_seconds()))
    traffic_in = float(row["traffic_in_mb"] or 0)
    traffic_out = float(row["traffic_out_mb"] or 0)
    return ProfileOpenSession(
        started_at=started,
        started_at_label=format_dt_msk(started, time_sep=" ") or "—",
        duration_label=format_session_duration(duration_sec),
        protocol=protocol,  # type: ignore[arg-type]
        ip_address=(row["ip_address"] or "—").strip(),
        station_name=(row["station_name"] or "").strip() or None,
        traffic_in_mb=traffic_in,
        traffic_out_mb=traffic_out,
        traffic_in_label=format_traffic_mb(traffic_in),
        traffic_out_label=format_traffic_mb(traffic_out),
    )


async def load_open_sessions(session: AsyncSession, login: str) -> list[ProfileOpenSession]:
    login = (login or "").strip()
    if not login:
        return []
    now = datetime.now(timezone.utc)
    r = await session.execute(text(_OPEN_SESSIONS_SQL), {"login": login})
    return [_row_to_open_session(row, now=now) for row in r.mappings().all()]


async def _call_radius_proc(session: AsyncSession, sql: str, params: dict[str, Any]) -> None:
    """PostgreSQL PROCEDURE — только CALL, не SELECT."""
    await session.execute(text(sql), params)


def _dt_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


async def _log_tariff_action(
    session: AsyncSession,
    *,
    operator: dict[str, Any],
    request: Request,
    user_id: int,
    action: str,
    details: Optional[dict[str, Any]] = None,
) -> None:
    await write_operator_log(
        session,
        operator_id=int(operator["user_id"]),
        action=action,
        subscriber_id=user_id,
        page=f"/users/{user_id}",
        request=request,
        subject_type="tariff",
        subject_id=user_id,
        details=details,
        auto_commit=False,
    )


async def force_disconnect(session: AsyncSession, user_id: int, login: str) -> ActionMessage:
    allowed, limit_msg = await check_disconnect_sessions_allowed(user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=limit_msg)
    if await count_open_sessions(session, login) < 1:
        raise HTTPException(status_code=400, detail="Нет активных сессий")
    await _call_radius_proc(
        session,
        "CALL radius.force_disconnect_one(:login)",
        {"login": login},
    )
    await session.commit()
    await record_disconnect_sessions_success(user_id)
    return ActionMessage(message="Сессии будут закрыты в течение минуты")


async def unfreeze_tariff(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> ActionMessage:
    await _require_physical_subscriber(session, user_id)
    await _assert_physical_can_unfreeze(session, user_id)
    await _call_radius_proc(session, "CALL radius.unfreeze_tariff(:uid)", {"uid": user_id})
    await _log_tariff_action(
        session,
        operator=operator,
        request=request,
        user_id=user_id,
        action="tariff.unfreeze",
    )
    await session.commit()
    await on_tariff_freeze_changed(session, user_id)
    return ActionMessage(message="Тариф разморожен")


async def delete_planned_freeze(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> ActionMessage:
    await _require_physical_subscriber(session, user_id)
    fr = await UserFreezeTariffDAO.find_one_or_none(session, user_id=user_id)
    if not fr:
        raise HTTPException(status_code=404, detail="Запланированная заморозка не найдена")
    if fr.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Тариф уже заморожен")
    await _log_tariff_action(
        session,
        operator=operator,
        request=request,
        user_id=user_id,
        action="tariff.freeze_plan.cancel",
        details={
            "date_freeze": _dt_iso(fr.get("date_freeze")),
            "date_unfreeze": _dt_iso(fr.get("date_unfreeze")),
        },
    )
    await session.execute(delete(UserFreezeTariff).where(UserFreezeTariff.user_id == user_id))
    await session.commit()
    await on_tariff_freeze_changed(session, user_id)
    return ActionMessage(message="Запланированная заморозка отменена")


async def apply_freeze(
    session: AsyncSession,
    user_id: int,
    date_freeze: Optional[datetime],
    date_unfreeze: Optional[datetime],
    operator: dict[str, Any],
    request: Request,
) -> ActionMessage:
    await _require_physical_subscriber(session, user_id)
    await _assert_physical_can_freeze(session, user_id)
    now = datetime.now(timezone.utc)
    immediate = date_freeze is None or date_freeze <= now

    if immediate:
        await _call_radius_proc(
            session,
            "CALL radius.freeze_tariff(:uid, :reason)",
            {"uid": user_id, "reason": "2"},
        )
        if date_unfreeze:
            fr = await UserFreezeTariffDAO.find_one_or_none(session, user_id=user_id)
            if fr:
                await UserFreezeTariffDAO.update(
                    session,
                    filter_by={"user_id": user_id},
                    date_unfreeze=date_unfreeze,
                )
        await _log_tariff_action(
            session,
            operator=operator,
            request=request,
            user_id=user_id,
            action="tariff.freeze",
            details={
                "immediate": True,
                "date_freeze": _dt_iso(date_freeze),
                "date_unfreeze": _dt_iso(date_unfreeze),
            },
        )
        await session.commit()
        await on_tariff_freeze_changed(session, user_id)
        return ActionMessage(message="Тариф заморожен")

    existing = await UserFreezeTariffDAO.find_one_or_none(session, user_id=user_id)
    if existing:
        await UserFreezeTariffDAO.update(
            session,
            filter_by={"user_id": user_id},
            is_frozen=False,
            reason_code=2,
            date_freeze=date_freeze,
            date_unfreeze=date_unfreeze,
        )
    else:
        await UserFreezeTariffDAO.add(
            session,
            user_id=user_id,
            is_frozen=False,
            reason_code=2,
            date_freeze=date_freeze,
            date_unfreeze=date_unfreeze,
        )
    await _log_tariff_action(
        session,
        operator=operator,
        request=request,
        user_id=user_id,
        action="tariff.freeze",
        details={
            "immediate": False,
            "date_freeze": _dt_iso(date_freeze),
            "date_unfreeze": _dt_iso(date_unfreeze),
        },
    )
    await session.commit()
    await on_tariff_freeze_changed(session, user_id)
    return ActionMessage(message="Заморозка запланирована")
