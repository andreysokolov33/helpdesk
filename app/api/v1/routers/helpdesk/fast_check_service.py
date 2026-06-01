"""Быстрая проверка абонента — цепочка шагов с приоритетом."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.fast_check_schemas import (
    FastCheckResponse,
    FastCheckStatus,
    FastCheckStep,
    ManagerContact,
)
from app.api.v1.routers.helpdesk.user_profile_service import (
    _load_freeze,
    _load_netflow,
    _load_personal,
)
from app.api.v1.routers.helpdesk.user_profile_utils import (
    PAY_TYPE_LABELS,
    freeze_info_html,
    resolve_freeze_reason_label,
)
from app.api.v1.routers.users.dao import UsersDAO
from app.models.users import FastCheckDatabase

_UNLIM_SESSION_LIMIT = 2

# Подписи шагов, если строка в fast_check_database отсутствует
_CHECK_LABEL_FALLBACK: dict[str, str] = {
    "account_status": "1. Статус учётной записи",
    "tariff_state": "2. Состояние тарифа",
    "balance_tariff": "3. Баланс и платежи",
    "station_aliveness": "4. Станция на связи",
    "active_sessions": "5. Активные сессии",
    "session_limit": "6. Лимит сессий",
}


@dataclass
class _Instr:
    check_label: str
    actions_html: str
    stop_on_fail: bool = True


@dataclass
class _Ctx:
    user_id: int
    login: str
    is_jur: int
    user_status: int
    balance: float
    id_grp: int
    auth_page: Optional[str]
    is_netflow: bool = False
    tariff_connected: bool = False
    real_type: Optional[str] = None
    groupname: Optional[str] = None


async def _load_instruction(
    session: AsyncSession,
    cache: dict[tuple[str, int], Optional[_Instr]],
    test_code: str,
    variant: int,
) -> Optional[_Instr]:
    key = (test_code, variant)
    if key not in cache:
        row = None
        variants_to_try = [variant]
        if test_code == "tariff_state" and variant == 7:
            variants_to_try.append(6)
        if 1 <= variant <= 7:
            variants_to_try.append(0)
        for v in variants_to_try:
            r = await session.execute(
                select(FastCheckDatabase).where(
                    FastCheckDatabase.test_code == test_code,
                    FastCheckDatabase.variant == v,
                    FastCheckDatabase.is_active.is_(True),
                )
            )
            row = r.scalar_one_or_none()
            if row:
                break
        cache[key] = (
            _Instr(row.check_label, row.actions_html, bool(row.stop_on_fail)) if row else None
        )
    return cache[key]


def _step(
    test_code: str,
    variant: int,
    status: FastCheckStatus,
    instr: Optional[_Instr],
    *,
    detail: Optional[str] = None,
    extra_html: str = "",
    stop_chain: Optional[bool] = None,
) -> FastCheckStep:
    label = (instr.check_label if instr else None) or _CHECK_LABEL_FALLBACK.get(
        test_code, test_code
    )
    html: Optional[str] = None
    if status in ("fail", "warn") and instr:
        html = instr.actions_html + (extra_html or "")
    elif status == "skip" and instr and extra_html:
        html = instr.actions_html + extra_html
    stop = stop_chain if stop_chain is not None else (
        status == "fail" and bool(instr.stop_on_fail if instr else True)
    )
    return FastCheckStep(
        test_code=test_code,
        variant=variant,
        check_label=label,
        status=status,
        detail=detail,
        actions_html=html,
        stop_chain=stop,
    )


def _stopped_at_label(steps: list[FastCheckStep]) -> str:
    for s in steps:
        if s.stop_chain and s.status in ("fail", "warn"):
            return s.check_label
    return steps[-1].check_label


def _fail_response(
    steps: list[FastCheckStep],
    managers: list[ManagerContact] | None = None,
) -> FastCheckResponse:
    return FastCheckResponse(
        steps=steps,
        stopped_at=_stopped_at_label(steps),
        manager_contacts=managers or [],
    )


async def _load_jur_managers(session: AsyncSession) -> list[ManagerContact]:
    try:
        r = await session.execute(
            text("""
                SELECT su.id, su.full_name
                FROM users.skystream_users su
                WHERE su.role = 'manager' AND su.is_active = true
                ORDER BY su.full_name NULLS LAST, su.id
                LIMIT 20
            """)
        )
        managers: list[ManagerContact] = []
        for row in r.mappings().all():
            mid = int(row["id"])
            phones = (
                await session.execute(
                    text(
                        "SELECT phone FROM users.skystream_user_phones"
                        " WHERE user_id = :mid ORDER BY is_primary DESC, id"
                    ),
                    {"mid": mid},
                )
            ).scalars().all()
            emails = (
                await session.execute(
                    text(
                        "SELECT email FROM users.skystream_user_emails"
                        " WHERE user_id = :mid ORDER BY is_primary DESC, id"
                    ),
                    {"mid": mid},
                )
            ).scalars().all()
            managers.append(
                ManagerContact(
                    full_name=(row["full_name"] or "").strip() or None,
                    phones=[str(p).strip() for p in phones if p],
                    emails=[str(e).strip() for e in emails if e],
                )
            )
        return [m for m in managers if m.phones or m.emails]
    except Exception:
        return []


def _session_detail_line(breakdown: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for row in breakdown:
        proto = (row.get("proto") or "").strip()
        cnt = int(row.get("cnt") or 0)
        if proto.upper() == "PPP":
            label = "PPPoE (роутер)"
        elif proto.lower() == "hotspot":
            label = "Hotspot (портал)"
        else:
            label = proto or "Подключение"
        parts.append(f"{label}: {cnt}")
    return ", ".join(parts)


def _payments_list_html(payments: list[dict[str, Any]], *, pending: bool) -> str:
    if not payments:
        return ""
    title = "Ожидают зачисления" if pending else "Не завершены"
    rows = "".join(
        f"<li>{p.get('date_in_tz')}: <strong>{p.get('amount')} ₽</strong> — "
        f"{PAY_TYPE_LABELS.get(str(p.get('type') or ''), str(p.get('type') or 'оплата'))}"
        f"{' (ожидание банка)' if pending else ''}</li>"
        for p in payments
    )
    return f'<p><strong>{title}:</strong></p><ul>{rows}</ul>'


def _managers_html(contacts: list[ManagerContact]) -> str:
    if not contacts:
        return '<p class="fc-note">Контакты менеджеров не найдены — уточните у старшего смены.</p>'
    parts = ['<div class="fc-managers"><h5>Менеджеры по работе с ЮЛ</h5><ul>']
    for m in contacts:
        name = m.full_name or "Менеджер"
        ph = ", ".join(m.phones) if m.phones else "—"
        em = ", ".join(m.emails) if m.emails else "—"
        parts.append(f"<li><strong>{name}</strong><br>Тел.: {ph}<br>E-mail: {em}</li>")
    parts.append("</ul></div>")
    return "".join(parts)


async def _build_ctx(session: AsyncSession, user_id: int) -> _Ctx:
    personal = await _load_personal(session, user_id)
    urow = await UsersDAO.find_one_or_none(session, id=user_id) or {}
    id_grp = int(urow.get("id_grp") or 0)
    netflow_note, _ = await _load_netflow(session, user_id)
    is_netflow = netflow_note is not None
    return _Ctx(
        user_id=user_id,
        login=personal.login,
        is_jur=personal.is_juridical,
        user_status=personal.user_status or 1,
        balance=float(urow.get("balanse") or 0),
        id_grp=id_grp,
        auth_page=personal.auth_page,
        is_netflow=is_netflow,
    )


async def _is_tariff_connected(session: AsyncSession, ctx: _Ctx) -> tuple[bool, Optional[str], Optional[str]]:
    if ctx.is_netflow:
        r = await session.execute(
            text("""
                SELECT 1 FROM service.service_jur_by_months sjbm
                WHERE sjbm.user_id = :uid
                  AND sjbm.year = extract(year FROM now())::int
                  AND sjbm.month = extract(month FROM now())::int
                LIMIT 1
            """),
            {"uid": ctx.user_id},
        )
        ok = r.scalar_one_or_none() is not None
        return ok, None, None

    r = await session.execute(
        text("""
            SELECT r.groupname, r.sname
            FROM radius.radusergroup r
            WHERE lower(r.username) = lower(:login)
            ORDER BY r.priority NULLS LAST
            LIMIT 1
        """),
        {"login": ctx.login},
    )
    row = r.mappings().one_or_none()
    if not row or not row.get("groupname"):
        return False, None, None
    gn = (row["groupname"] or "").strip().lower()
    if gn == "disabled":
        return False, gn, row.get("sname")
    return True, gn, row.get("sname")


async def _has_radreply(session: AsyncSession, login: str) -> bool:
    r = await session.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM radius.radreply rr
                WHERE lower(rr.username) = lower(:login)
                  AND NULLIF(trim(rr.value), '') IS NOT NULL
            )
        """),
        {"login": login},
    )
    return bool(r.scalar())


async def _has_radreply_unlim(session: AsyncSession, user_id: int) -> bool:
    r = await session.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM radius.radreply_unlim ru
                WHERE ru.uid = :uid
                  AND (ru.now_day_traffic IS NOT NULL OR ru.full_packet IS NOT NULL)
            )
        """),
        {"uid": user_id},
    )
    return bool(r.scalar())


async def _load_real_type(session: AsyncSession, sname: Optional[str]) -> Optional[str]:
    if not sname:
        return None
    r = await session.execute(
        text("SELECT real_type::text FROM service.service WHERE sname = :sn LIMIT 1"),
        {"sn": sname},
    )
    return r.scalar_one_or_none()


async def _min_tariff_price(session: AsyncSession, id_grp: int) -> Optional[float]:
    if not id_grp:
        return None
    r = await session.execute(
        text("""
            WITH sat AS (
                SELECT cs.satellite_id
                FROM wifitochka.ip_group ig
                JOIN stations.ip_group_channel igc ON igc.id = ig.channel_id
                JOIN stations.channel_satellite cs ON cs.channel_id = igc.id
                WHERE ig.id = :gid
                LIMIT 1
            ),
            base AS (
                SELECT s.price::numeric AS p
                FROM wifitochka.grp_srv gs
                JOIN service.service s ON s.id = gs.id_srv
                WHERE gs.id_grp = :gid
                  AND coalesce(s.active, 0) = 1
                  AND coalesce(s.hidden, 0) = 0
                  AND s.price IS NOT NULL
            ),
            slider_lim AS (
                SELECT stl.price::numeric AS p
                FROM service.slider_tariffs_limited stl
                CROSS JOIN sat
                WHERE stl.satellite_id = sat.satellite_id AND stl.active = true
            ),
            slider_unlim AS (
                SELECT stu.price::numeric AS p
                FROM service.slider_tariffs_unlimited stu
                CROSS JOIN sat
                WHERE stu.satellite_id = sat.satellite_id AND stu.active = true
            )
            SELECT min(p)::float FROM (
                SELECT p FROM base
                UNION ALL SELECT p FROM slider_lim
                UNION ALL SELECT p FROM slider_unlim
            ) allp
        """),
        {"gid": id_grp},
    )
    val = r.scalar_one_or_none()
    return float(val) if val is not None else None


async def _recent_payments(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    r = await session.execute(
        text("""
            SELECT amount, date_in_tz, state, type
            FROM payments.pays p
            WHERE p.uid = :uid
              AND p.date_in_tz > now() - interval '1 day'
              AND p.state IN ('canceled', 'in')
            ORDER BY date_in_tz DESC
            LIMIT 10
        """),
        {"uid": user_id},
    )
    return [dict(row) for row in r.mappings().all()]


async def _station_check_needed(session: AsyncSession, id_grp: int) -> tuple[bool, Optional[bool]]:
    """(needs_check, is_alive). needs_check=False → пропуск."""
    if not id_grp:
        return False, None
    r = await session.execute(
        text("""
            SELECT coalesce(d.has_form, false) AS has_form
            FROM wifitochka.ip_group ig
            LEFT JOIN partner.diler d ON d.id = ig.id_diler
            WHERE ig.id = :gid
        """),
        {"gid": id_grp},
    )
    row = r.mappings().one_or_none()
    if not row or not row.get("has_form"):
        return False, None
    alive_r = await session.execute(
        text("SELECT is_alive FROM stations.aliveness_status WHERE station_id = :sid"),
        {"sid": id_grp},
    )
    alive = alive_r.scalar_one_or_none()
    return True, bool(alive) if alive is not None else False


async def _session_breakdown(session: AsyncSession, login: str) -> list[dict[str, Any]]:
    r = await session.execute(
        text("""
            SELECT coalesce(nullif(trim(framedprotocol), ''), 'Hotspot') AS proto, count(1)::int AS cnt
            FROM radius.radacct r
            WHERE lower(username) = lower(:login) AND acctstoptime IS NULL
            GROUP BY 1
        """),
        {"login": login},
    )
    return [dict(row) for row in r.mappings().all()]


async def run_fast_check(session: AsyncSession, user_id: int) -> FastCheckResponse:
    cache: dict[tuple[str, int], Optional[_Instr]] = {}
    ctx = await _build_ctx(session, user_id)
    steps: list[FastCheckStep] = []
    managers: list[ManagerContact] = []
    run_balance_after_tariff_fail = False

    # --- 1. Статус УЗ ---
    if ctx.user_status == 3:
        variant = 23 if ctx.is_jur == 2 else 3
        instr = await _load_instruction(session, cache, "account_status", variant)
        extra = ""
        if ctx.is_jur == 2:
            managers = await _load_jur_managers(session)
            extra = _managers_html(managers)
        steps.append(
            _step("account_status", variant, "fail", instr, stop_chain=True, extra_html=extra)
        )
        return _fail_response(steps, managers)

    instr = await _load_instruction(session, cache, "account_status", 0)
    status_word = "Активен" if ctx.user_status == 1 else "Заморожен" if ctx.user_status == 2 else "Допустим"
    steps.append(
        _step("account_status", 0, "pass", instr, detail=status_word)
    )

    # --- 2. Тариф ---
    freeze = await _load_freeze(session, user_id)
    if freeze and freeze.get("is_frozen"):
        variant = 25 if ctx.is_jur == 2 else 5
        instr = await _load_instruction(session, cache, "tariff_state", variant)
        reason = await resolve_freeze_reason_label(session, freeze)
        extra = freeze_info_html(freeze, reason)
        if ctx.is_jur == 2:
            managers = managers or await _load_jur_managers(session)
            extra += _managers_html(managers)
        steps.append(_step("tariff_state", variant, "fail", instr, stop_chain=True, extra_html=extra))
        return _fail_response(steps, managers)

    connected, groupname, sname = await _is_tariff_connected(session, ctx)
    ctx.tariff_connected = connected
    ctx.groupname = groupname
    if sname:
        ctx.real_type = await _load_real_type(session, sname)

    if not connected:
        tariff_ended = (ctx.groupname or "").strip().lower() == "disabled"
        variant = 26 if ctx.is_jur == 2 else (7 if tariff_ended else 6)
        instr = await _load_instruction(session, cache, "tariff_state", variant)
        extra = ""
        if ctx.is_jur == 2:
            managers = await _load_jur_managers(session)
            extra = _managers_html(managers)
        detail = "Тариф закончился" if tariff_ended and ctx.is_jur == 0 else None
        steps.append(
            _step(
                "tariff_state",
                variant,
                "fail",
                instr,
                detail=detail,
                stop_chain=False,
                extra_html=extra,
            )
        )
        run_balance_after_tariff_fail = ctx.is_jur == 0
        if ctx.is_jur == 2:
            return _fail_response(steps, managers)
    else:
        rt = ctx.real_type or "default"
        if rt == "default":
            has_reply = await _has_radreply(session, ctx.login)
            if not has_reply:
                instr = await _load_instruction(session, cache, "tariff_state", 2)
                steps.append(_step("tariff_state", 2, "fail", instr, stop_chain=True))
                return _fail_response(steps)
            instr = await _load_instruction(session, cache, "tariff_state", 1)
            steps.append(
                _step("tariff_state", 1, "pass", instr, detail="Трафик в пакете доступен")
            )
        elif rt == "unlim_fap":
            has_unlim = await _has_radreply_unlim(session, ctx.user_id)
            if not has_unlim:
                instr = await _load_instruction(session, cache, "tariff_state", 4)
                steps.append(
                    _step(
                        "tariff_state",
                        4,
                        "warn",
                        instr,
                        detail="Суточный объём исчерпан, скорость ограничена",
                        stop_chain=False,
                    )
                )
            else:
                instr = await _load_instruction(session, cache, "tariff_state", 3)
                steps.append(
                    _step("tariff_state", 3, "pass", instr, detail="Полная скорость")
                )
        else:
            instr = await _load_instruction(session, cache, "tariff_state", 1)
            steps.append(_step("tariff_state", 1, "pass", instr, detail="Тариф подключен и активен"))

    # --- 3. Баланс и платежи (всегда в цепочке) ---
    if run_balance_after_tariff_fail:
        min_price = await _min_tariff_price(session, ctx.id_grp)
        pays = await _recent_payments(session, user_id)
        canceled = [p for p in pays if p.get("state") == "canceled"]
        pending = [p for p in pays if p.get("state") == "in"]
        mp = f"{min_price:.2f}" if min_price is not None else None
        sufficient = min_price is not None and ctx.balance >= min_price

        if sufficient and not canceled and not pending:
            instr = await _load_instruction(session, cache, "balance_tariff", 0)
            steps.append(
                _step(
                    "balance_tariff",
                    0,
                    "pass",
                    instr,
                    detail=f"Баланс {ctx.balance:.2f} ₽, достаточно для подключения тарифа",
                    stop_chain=False,
                )
            )
            return FastCheckResponse(
                steps=steps,
                stopped_at=next(
                    s.check_label for s in steps if s.test_code == "tariff_state"
                ),
                manager_contacts=managers,
            )
        else:
            extra = ""
            if mp:
                extra += (
                    f"<p>Баланс: <strong>{ctx.balance:.2f} ₽</strong>, "
                    f"нужно от <strong>{mp} ₽</strong> для минимального тарифа.</p>"
                )
            extra += _payments_list_html(canceled, pending=False)
            extra += _payments_list_html(pending, pending=True)

            if pending:
                instr = await _load_instruction(session, cache, "balance_tariff", 4)
                steps.append(
                    _step(
                        "balance_tariff",
                        4,
                        "fail",
                        instr,
                        detail="Недостаточно средств или платёж не зачислен",
                        extra_html=extra,
                        stop_chain=True,
                    )
                )
            elif canceled:
                instr = await _load_instruction(session, cache, "balance_tariff", 3)
                steps.append(
                    _step(
                        "balance_tariff",
                        3,
                        "fail",
                        instr,
                        detail="Недостаточно средств, есть неудачные оплаты",
                        extra_html=extra,
                        stop_chain=True,
                    )
                )
            else:
                instr = await _load_instruction(session, cache, "balance_tariff", 1)
                steps.append(
                    _step(
                        "balance_tariff",
                        1,
                        "fail",
                        instr,
                        detail=f"Баланс {ctx.balance:.2f} ₽ — недостаточно для подключения тарифа",
                        extra_html=extra,
                        stop_chain=True,
                    )
                )
            return _fail_response(steps)
    else:
        instr = await _load_instruction(session, cache, "balance_tariff", 8)
        steps.append(
            _step("balance_tariff", 8, "skip", instr, detail="Тариф подключен — проверка не требуется")
        )

    # --- 4. Станция ---
    needs_st, is_alive = await _station_check_needed(session, ctx.id_grp)
    if not needs_st:
        instr = await _load_instruction(session, cache, "station_aliveness", 8)
        steps.append(
            _step("station_aliveness", 8, "skip", instr, detail="Для этого типа станции не проверяется")
        )
    elif is_alive:
        instr = await _load_instruction(session, cache, "station_aliveness", 0)
        steps.append(_step("station_aliveness", 0, "pass", instr, detail="Станция на связи"))
    else:
        instr = await _load_instruction(session, cache, "station_aliveness", 1)
        steps.append(_step("station_aliveness", 1, "fail", instr, stop_chain=True))
        return _fail_response(steps)

    # --- 5. Сессии ---
    breakdown = await _session_breakdown(session, ctx.login)
    total = sum(int(x["cnt"]) for x in breakdown)
    if total == 0:
        instr = await _load_instruction(session, cache, "active_sessions", 1)
        extra = ""
        if ctx.auth_page:
            addr = str(ctx.auth_page).strip()
            extra += (
                '<p class="fc-hotspot-auth">'
                '<span class="fc-hotspot-auth__label">Страница авторизации для Hotspot:</span>'
                f'<span class="fc-hotspot-auth__addr">{addr}</span></p>'
            )
        steps.append(
            _step(
                "active_sessions",
                1,
                "fail",
                instr,
                detail="Нет активного подключения к сети",
                extra_html=extra,
                stop_chain=True,
            )
        )
        return _fail_response(steps)
    detail = _session_detail_line(breakdown)
    instr = await _load_instruction(session, cache, "active_sessions", 0)
    steps.append(
        _step("active_sessions", 0, "pass", instr, detail=f"Активных сессий: {total} ({detail})")
    )

    # --- 6. Лимит сессий (безлимит) ---
    if ctx.real_type == "unlim_fap" and total >= _UNLIM_SESSION_LIMIT:
        instr = await _load_instruction(session, cache, "session_limit", 1)
        steps.append(
            _step(
                "session_limit",
                1,
                "fail",
                instr,
                detail=f"Открыто сессий: {total} (лимит {_UNLIM_SESSION_LIMIT})",
                stop_chain=True,
            )
        )
        return _fail_response(steps)

    if ctx.real_type != "unlim_fap":
        instr = await _load_instruction(session, cache, "session_limit", 8)
        steps.append(
            _step("session_limit", 8, "skip", instr, detail="Для лимитного тарифа не проверяется")
        )
    else:
        instr = await _load_instruction(session, cache, "session_limit", 0)
        steps.append(_step("session_limit", 0, "pass", instr, detail="В пределах лимита"))

    return FastCheckResponse(steps=steps, manager_contacts=managers)
