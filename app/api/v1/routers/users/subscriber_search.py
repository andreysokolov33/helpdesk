"""Поиск абонентов (users.user) — разбитые ORM-запросы для скорости."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oss import JurClientList
from app.models.stations import IpGroup
from app.models.users import User, UserDetails

_DIGITS_RE = re.compile(r"\D+")


def _normalize_pattern(pattern: str) -> tuple[str, str, str | None]:
    """(raw_trimmed, lower_pattern, digits_only_or_none)."""
    raw = pattern.strip()
    if len(raw) < 2:
        return raw, "", None
    pl = raw.lower()
    digits = _DIGITS_RE.sub("", raw)
    return raw, pl, digits if len(digits) >= 4 else None


def _like(lower_pattern: str) -> str:
    return f"%{lower_pattern}%"


def _latest_user_details_subq():
    """
    Одна строка user_details на абонента: сначала is_actual=true, иначе последняя по id.
    """
    rn = func.row_number().over(
        partition_by=UserDetails.user_id,
        order_by=(UserDetails.is_actual.desc().nulls_last(), UserDetails.id.desc()),
    )
    return (
        select(
            UserDetails.user_id.label("ud_user_id"),
            UserDetails.surname.label("ud_surname"),
            UserDetails.name.label("ud_name"),
            UserDetails.patronymic.label("ud_patronymic"),
            UserDetails.pas_series.label("ud_pas_series"),
            UserDetails.pas_number.label("ud_pas_number"),
            rn.label("ud_rn"),
        )
    ).subquery("ud_latest")


def _join_latest_ud(ud_sq, user_model=User):
    return and_(ud_sq.c.ud_user_id == user_model.id, ud_sq.c.ud_rn == 1)


def _format_passport(pas_series: str | None, pas_number: str | None, user_passport: str | None) -> str | None:
    series = (pas_series or "").strip()
    number = (pas_number or "").strip()
    if series and number:
        return f"{series} {number}"
    if series:
        return series
    if number:
        return number
    legacy = (user_passport or "").strip()
    return legacy or None


def _passport_sql(ud_sq, user_model=User):
    """Паспорт в SQL: trim по полям, fallback на users.user.passport."""
    series = func.trim(func.coalesce(ud_sq.c.ud_pas_series, ""))
    number = func.trim(func.coalesce(ud_sq.c.ud_pas_number, ""))
    from_details = case(
        (and_(series != "", number != ""), func.concat(series, " ", number)),
        (series != "", series),
        (number != "", number),
        else_=None,
    )
    legacy = func.nullif(func.trim(func.coalesce(user_model.passport, "")), "")
    return func.coalesce(from_details, legacy)


def _subscriber_columns(ud_sq):
    """Поля для отображения в результатах поиска."""
    jcl = JurClientList
    u = User

    fio = func.trim(
        func.concat_ws(
            " ",
            func.coalesce(ud_sq.c.ud_surname, ""),
            func.coalesce(ud_sq.c.ud_name, ""),
            func.coalesce(ud_sq.c.ud_patronymic, ""),
        )
    )

    name = case(
        (u.is_juridical == 0, case((fio != "", fio), else_=u.full_name)),
        (u.is_juridical == 2, jcl.short_name_organization),
        else_=u.full_name,
    ).label("name")

    email = case(
        (u.is_juridical == 0, u.email),
        else_=jcl.email_organization,
    ).label("email")

    phone = case(
        (u.is_juridical == 0, u.mob_tel),
        else_=jcl.phone_organization,
    ).label("phone")

    id_doc = case(
        (u.is_juridical == 0, _passport_sql(ud_sq, u)),
        else_=func.nullif(func.trim(func.coalesce(jcl.inn, "")), ""),
    ).label("id_doc")

    station_id = case(
        (u.id_grp > 0, u.id_grp),
        else_=None,
    ).label("station_id")
    hotspot_id = case(
        (IpGroup.id_hotspot > 0, IpGroup.id_hotspot),
        else_=None,
    ).label("hotspot_id")

    return (
        u.id.label("id"),
        u.login.label("login"),
        u.is_juridical.label("is_juridical"),
        ud_sq.c.ud_pas_series.label("pas_series"),
        ud_sq.c.ud_pas_number.label("pas_number"),
        u.passport.label("user_passport"),
        name,
        email,
        phone,
        id_doc,
        station_id,
        hotspot_id,
    )


def _row_to_hit(row: Any) -> dict[str, Any]:
    is_jur = int(row.is_juridical or 0)
    if is_jur == 0:
        id_doc = _format_passport(
            getattr(row, "pas_series", None),
            getattr(row, "pas_number", None),
            getattr(row, "user_passport", None),
        )
        if not id_doc:
            id_doc = (row.id_doc or "").strip() or None
    else:
        id_doc = (row.id_doc or "").strip() or None

    station_id = getattr(row, "station_id", None)
    hotspot_id = getattr(row, "hotspot_id", None)
    return {
        "id": int(row.id),
        "login": (row.login or "").strip(),
        "name": (row.name or "").strip(),
        "email": (row.email or "").strip() or None,
        "phone": (row.phone or "").strip() or None,
        "id_doc": id_doc,
        "is_juridical": is_jur,
        "station_id": int(station_id) if station_id else None,
        "hotspot_id": int(hotspot_id) if hotspot_id else None,
    }


def _hit_matches_pattern(hit: dict[str, Any], pl: str, digits: str | None) -> bool:
    """
    Оставляем только те строки, где паттерн виден в полях, которые отдаём в UI.
    """
    haystacks = [
        str(hit["id"]),
        hit.get("login") or "",
        hit.get("name") or "",
        hit.get("email") or "",
        hit.get("phone") or "",
        hit.get("id_doc") or "",
    ]
    if any(pl in (s or "").lower() for s in haystacks):
        return True
    if digits:
        digit_hay = [_DIGITS_RE.sub("", s or "") for s in haystacks]
        return any(digits in d for d in digit_hay)
    return False


async def _fetch(
    session: AsyncSession,
    stmt,
    seen: set[int],
    out: list[dict[str, Any]],
    limit: int,
    pl: str,
    digits: str | None,
) -> None:
    if len(out) >= limit:
        return
    result = await session.execute(stmt)
    for row in result.all():
        uid = int(row.id)
        if uid in seen:
            continue
        hit = _row_to_hit(row)
        if not _hit_matches_pattern(hit, pl, digits):
            continue
        seen.add(uid)
        out.append(hit)
        if len(out) >= limit:
            return


async def run_subscriber_search(
    session: AsyncSession,
    pattern: str,
    limit: int = 15,
) -> list[dict[str, Any]]:
    raw, pl, digits = _normalize_pattern(pattern)
    if len(raw) < 2:
        return []

    like = _like(pl)
    ud_sq = _latest_user_details_subq()
    ud_join = _join_latest_ud(ud_sq)
    cols = _subscriber_columns(ud_sq)
    u = User
    jcl = JurClientList
    ig = IpGroup
    ig_join = ig.id == u.id_grp

    seen: set[int] = set()
    out: list[dict[str, Any]] = []

    series = func.trim(func.coalesce(ud_sq.c.ud_pas_series, ""))
    number = func.trim(func.coalesce(ud_sq.c.ud_pas_number, ""))
    passport_sql = _passport_sql(ud_sq, u)
    passport_lower = func.lower(passport_sql)

    # 1. Точный ID (PK)
    if pl.isdigit():
        uid = int(pl)
        stmt = (
            select(*cols)
            .select_from(u)
            .outerjoin(ud_sq, ud_join)
            .outerjoin(ig, ig_join)
            .outerjoin(jcl, jcl.id == u.juridical_id)
            .where(u.id == uid)
            .limit(1)
        )
        await _fetch(session, stmt, seen, out, limit, pl, digits)
        if len(out) >= limit:
            return out

    # 2. Поля users.user
    user_conds = [
        func.lower(u.login).like(like),
        func.lower(u.email).like(like),
        func.lower(u.mob_tel).like(like),
        func.lower(u.home_tel).like(like),
        func.lower(u.work_tel).like(like),
        func.lower(func.coalesce(u.passport, "")).like(like),
        passport_lower.like(like),
    ]
    user_conds.append(
        and_(
            func.lower(func.coalesce(u.full_name, "")).like(like),
            ud_sq.c.ud_user_id.is_(None),
        )
    )
    if digits:
        digit_like = f"%{digits}%"
        user_conds.extend(
            [
                func.regexp_replace(func.coalesce(u.mob_tel, ""), r"\D", "", "g").like(digit_like),
                func.regexp_replace(func.coalesce(u.home_tel, ""), r"\D", "", "g").like(digit_like),
                func.regexp_replace(func.coalesce(u.work_tel, ""), r"\D", "", "g").like(digit_like),
            ]
        )

    stmt_user = (
        select(*cols)
        .select_from(u)
        .outerjoin(ud_sq, ud_join)
        .outerjoin(ig, ig_join)
        .outerjoin(jcl, jcl.id == u.juridical_id)
        .where(or_(*user_conds))
        .distinct(u.id)
        .order_by(u.id)
        .limit(limit)
    )
    await _fetch(session, stmt_user, seen, out, limit, pl, digits)
    if len(out) >= limit:
        return out

    # 3. user_details (ФИО, паспорт по полям)
    fio_lower = func.lower(
        func.trim(
            func.concat_ws(
                " ",
                func.coalesce(ud_sq.c.ud_surname, ""),
                func.coalesce(ud_sq.c.ud_name, ""),
                func.coalesce(ud_sq.c.ud_patronymic, ""),
            )
        )
    )
    passport_compact = func.lower(func.concat(series, number))

    details_conds = [
        fio_lower.like(like),
        passport_lower.like(like),
        passport_compact.like(like.replace(" ", "")),
        func.lower(func.coalesce(ud_sq.c.ud_surname, "")).like(like),
        func.lower(func.coalesce(ud_sq.c.ud_name, "")).like(like),
        func.lower(func.coalesce(ud_sq.c.ud_patronymic, "")).like(like),
        series.like(like),
        number.like(like),
    ]

    stmt_details = (
        select(*cols)
        .select_from(u)
        .join(ud_sq, ud_join)
        .outerjoin(ig, ig_join)
        .outerjoin(jcl, jcl.id == u.juridical_id)
        .where(or_(*details_conds))
        .distinct(u.id)
        .order_by(u.id)
        .limit(limit - len(out))
    )
    await _fetch(session, stmt_details, seen, out, limit, pl, digits)
    if len(out) >= limit:
        return out

    # 4. Юрлица
    jur_conds = [
        func.lower(jcl.short_name_organization).like(like),
        func.lower(jcl.name_organization).like(like),
        func.lower(jcl.inn).like(like),
        func.lower(jcl.email_organization).like(like),
        func.lower(jcl.phone_organization).like(like),
    ]
    if digits:
        jur_conds.append(
            func.regexp_replace(func.coalesce(jcl.phone_organization, ""), r"\D", "", "g").like(
                f"%{digits}%"
            )
        )

    stmt_jur = (
        select(*cols)
        .select_from(u)
        .outerjoin(ud_sq, ud_join)
        .outerjoin(ig, ig_join)
        .join(jcl, jcl.id == u.juridical_id)
        .where(or_(*jur_conds))
        .distinct(u.id)
        .order_by(u.id)
        .limit(limit - len(out))
    )
    await _fetch(session, stmt_jur, seen, out, limit, pl, digits)

    return out
