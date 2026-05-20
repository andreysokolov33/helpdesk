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
    ProfilePersonal,
    ProfileTariffActive,
    ProfileTicket,
    ProfileTicketListResponse,
    TariffBlockResponse,
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
    jur_frozen_traffic_mb,
    jur_traffic_overrun_mb,
    parse_speed_line,
    pick_rate_limit,
    tariff_display_name,
    traffic_reset_labels,
)
from app.api.v1.routers.helpdesk.operator_log_service import write_operator_log
from app.api.v1.routers.users.dao import RadacctDAO, UserFreezeTariffDAO, UsersDAO
from app.core.user_cache import on_tariff_freeze_changed, on_unarchive
from app.api.v1.routers.users.subscriber_search import _format_passport
from app.constants import STATUS_DISPLAY, SUPPORT_LINE_DISPLAY
from app.models.users import TrackerTickets, User, UserDetails, UserFreezeTariff

_ENTITY = {0: "Физическое лицо", 1: "Физическое лицо", 2: "Юридическое лицо"}
_STATUS = {1: "Активен", 2: "Заморожен", 3: "В архиве"}


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
                    jcl.short_name_organization,
                    jcl.email_organization,
                    jcl.phone_organization,
                    jcl.inn,
                    coalesce(sf.station_name, ig.name) AS station_name,
                    h.ip AS auth_page
                FROM users."user" u
                LEFT JOIN LATERAL (
                    SELECT ud.surname, ud.name, ud.patronymic, ud.pas_series, ud.pas_number
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
    if is_jur == 2:
        name = (row["short_name_organization"] or row["full_name"] or "").strip()
        email = row["email_organization"]
        phone = row["phone_organization"]
        id_doc = (row["inn"] or "").strip() or None
    else:
        parts = [row["ud_surname"], row["ud_name"], row["ud_patronymic"]]
        name = " ".join(p for p in parts if p and str(p).strip()).strip() or (row["full_name"] or "")
        email = row["email"]
        phone = row["mob_tel"]
        id_doc = _format_passport(row["ud_pas_series"], row["ud_pas_number"], row["passport"])

    us = int(row["user_status"]) if row["user_status"] is not None else 1
    personal = ProfilePersonal(
        user_id=int(row["id"]),
        name=name or f"#{row['id']}",
        login=(row["login"] or "").strip(),
        email=(email or "").strip() or None,
        phone=(phone or "").strip() or None,
        id_doc=id_doc,
        is_juridical=is_jur,
        entity_label=_ENTITY.get(is_jur, "Физическое лицо"),
        user_status=us,
        status_label=_STATUS.get(us, "Неизвестно"),
        station_name=row["station_name"],
        auth_page=row["auth_page"],
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
                CASE WHEN r.groupname = 'disabled' THEN 0 ELSE 1 END AS is_active,
                usd.traffic_renew_count,
                usd.valid_date,
                u.traffic_update_hour AS msk_hour,
                ig.gmt,
                ru.now_day_traffic AS unlim_day_traffic
            FROM users."user" u
            LEFT JOIN LATERAL (
                SELECT r.groupname, r.sname, r.priority
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


def _build_tariff(
    trow: Optional[dict[str, Any]],
    freeze: Optional[dict[str, Any]],
    is_jur: int,
    *,
    service_meta: Optional[dict[str, Any]] = None,
    jur_normal: Optional[int] = None,
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
            can_unfreeze=is_fl,
            can_freeze=False,
            can_cancel_planned_freeze=False,
            can_disconnect_sessions=False,
        )

    if not trow and not freeze:
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

    state = "active" if is_active else "inactive"
    if planned:
        state = "planned_freeze"

    return ProfileTariffActive(
        state=state,
        tariff_name=(trow or {}).get("tariff_name") or (freeze.get("tariff") if freeze else "—"),
        real_type=real_type,
        is_active=is_active,
        rate_up=format_speed_display(up),
        rate_down=format_speed_display(down),
        speed_unlimited=real_type == "unlim_fap",
        remain_traffic_mb=bytes_to_mb(remain),
        full_packet_mb=bytes_to_mb(full),
        disconnect_at_label=disconnect_label,
        valid_date_label=format_dt_msk(valid_date),
        jur_main_packet_mb=jur_main_mb,
        jur_dop_packet_mb=jur_dop_mb,
        overrun_mb=overrun,
        traffic_renew_count=renew,
        msk_reset=msk_reset,
        local_reset=local_reset,
        planned_freeze_at=format_dt_msk(freeze.get("date_freeze")) if planned else None,
        unfreeze_at=format_dt_msk(freeze.get("date_unfreeze")) if planned else None,
        can_freeze=is_fl and is_active and not planned,
        can_unfreeze=False,
        can_cancel_planned_freeze=is_fl and planned,
    )


_TICKETS_BASE_WHERE = "tt.user_id = :uid"

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
    ORDER BY
        CASE WHEN tt.status::text IN ('open', 'in_progress') THEN 0 ELSE 1 END,
        tt.date_of_create DESC
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
    return ProfileTicketListResponse(total=total, page=page, per_page=per_page, items=items)


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
    total = int(
        (
            await session.execute(
                text(
                    """
                    SELECT count(*)::int
                    FROM payments.pays p
                    WHERE p.uid = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).scalar_one()
        or 0
    )
    offset = (page - 1) * per_page
    r = await session.execute(
        text(
            """
            SELECT
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
            ORDER BY msk_date DESC NULLS LAST
            LIMIT :limit OFFSET :offset
            """
        ),
        {"uid": user_id, "limit": per_page, "offset": offset},
    )
    items = [_row_to_payment_item(row) for row in r.mappings().all()]
    return PaymentHistoryListResponse(total=total, page=page, per_page=per_page, items=items)


_TARIFF_HISTORY_COUNT = """
    SELECT (
        (SELECT count(*)::int FROM service.activated_services WHERE uid = :uid)
        + (SELECT count(*)::int FROM service.activated_dops WHERE uid = :uid)
    ) AS total
"""

_TARIFF_HISTORY_PAGE = """
    WITH combined AS (
        SELECT
            t.activation_timestamp AS activated_at,
            'tariff'::text AS row_kind,
            s.real_type::text AS real_type,
            t.deactivation_date,
            t.packet_size,
            t.days,
            t.price,
            NULL::text AS dop_name,
            t.sname
        FROM service.activated_services t
        LEFT JOIN service.service s ON s.sname = t.sname
        WHERE t.uid = :uid
        UNION ALL
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
    )
    SELECT * FROM combined
    ORDER BY activated_at DESC NULLS LAST
    LIMIT :limit OFFSET :offset
"""


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


async def load_user_tariff_history_page(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
) -> TariffHistoryListResponse:
    total = int(
        (await session.execute(text(_TARIFF_HISTORY_COUNT), {"uid": user_id})).scalar_one()
        or 0
    )
    offset = (page - 1) * per_page
    r = await session.execute(
        text(_TARIFF_HISTORY_PAGE),
        {"uid": user_id, "limit": per_page, "offset": offset},
    )
    items = [_row_to_tariff_history_item(row) for row in r.mappings().all()]
    return TariffHistoryListResponse(total=total, page=page, per_page=per_page, items=items)


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
    tariff = _build_tariff(
        trow,
        freeze,
        personal.is_juridical,
        service_meta=service_meta,
        jur_normal=jur_normal,
    )
    return tariff, netflow_note, netflow_tariff


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

    return UserProfileResponse(
        personal=personal,
        online=online,
        open_sessions_count=open_sessions,
        balance=balance,
        tariff=tariff,
        netflow_note=netflow_note,
        netflow_tariff=netflow_tariff,
        health_check=health,
        tickets=tickets,
    )


async def remove_ended_tariff(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> TariffBlockResponse:
    """Отключение завершённого тарифа (radius.remove_user) для ФЛ и ЮЛ."""
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
    await _require_physical_subscriber(session, user_id)
    n = await UsersDAO.update(
        session,
        filter_by={"id": user_id},
        user_status=1,
        archive=0,
    )
    if not n:
        raise HTTPException(status_code=404, detail="Абонент не найден")
    await on_unarchive(session, user_id)
    return ActionMessage(message="Учётная запись восстановлена")


async def count_open_sessions(session: AsyncSession, login: str) -> int:
    _online, open_count, _last = await RadacctDAO.get_session_summary(session, login)
    return open_count


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


async def force_disconnect(session: AsyncSession, login: str) -> ActionMessage:
    if await count_open_sessions(session, login) < 1:
        raise HTTPException(status_code=400, detail="Нет активных сессий")
    await _call_radius_proc(
        session,
        "CALL radius.force_disconnect_one(:login)",
        {"login": login},
    )
    await session.commit()
    return ActionMessage(message="Сессии будут закрыты в течение минуты")


async def unfreeze_tariff(
    session: AsyncSession,
    user_id: int,
    operator: dict[str, Any],
    request: Request,
) -> ActionMessage:
    await _require_physical_subscriber(session, user_id)
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
