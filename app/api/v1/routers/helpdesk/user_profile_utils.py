"""Утилиты форматирования для карточки абонента."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

_MSK = ZoneInfo("Europe/Moscow")

PAY_TYPE_LABELS: dict[str, str] = {
    "qr": "QR",
    "yandex": "ЮMoney",
    "sberbank": "Сбербанк",
    "gazprom": "Газпромбанк",
    "alfa": "Альфа-Банк",
}

PAY_STATE_LABELS: dict[str, str] = {
    "payed": "Оплачено",
    "canceled": "Отменено",
    "in": "В обработке",
    "refund": "Возврат",
}


def bytes_to_mb(value: int | None) -> float:
    if value is None:
        return 0.0
    return round(int(value) / (1024 * 1024), 1)


def format_mb(value: int | None) -> str:
    mb = bytes_to_mb(value)
    if mb >= 1000:
        return f"{mb:,.0f}".replace(",", " ") + " МБ"
    return f"{mb:,.1f}".replace(",", " ").replace(".0 ", " ") + " МБ"


def format_seconds_remaining(seconds: int | None) -> str:
    if not seconds or seconds <= 0:
        return "—"
    days, rem = divmod(int(seconds), 86400)
    hours, mins = divmod(rem, 3600)
    mins //= 60
    if days:
        return f"{days} дн., {hours:02d}:{mins:02d}"
    return f"{hours:02d}:{mins:02d}"


def parse_speed_line(rate: str | None) -> tuple[str, str]:
    """
    '512k/2M' -> (upload, download) человекочитаемо.
    Первая часть — обратный канал, вторая — прямой.
    """
    if not rate or not str(rate).strip():
        return ("—", "—")
    parts = str(rate).strip().split("/", 1)
    up = _format_speed_token(parts[0]) if parts else "—"
    down = _format_speed_token(parts[1]) if len(parts) > 1 else "—"
    return (up, down)


def pick_rate_limit(rate: str | None, u_slow_rate: str | None, now_day_traffic: int | None) -> str:
    """Безлимит: при нулевом дневном трафике — u_slow_rate (первый блок)."""
    if now_day_traffic is not None and int(now_day_traffic) <= 0 and u_slow_rate:
        chunk = str(u_slow_rate).strip().split()[0]
        return chunk or (rate or "")
    return rate or ""


def _format_speed_token(token: str) -> str:
    t = token.strip()
    if not t:
        return "—"
    m = re.match(r"^([\d.]+)\s*([kKmMgG])", t)
    if not m:
        return t
    num, unit = m.group(1), m.group(2).upper()
    label = {"K": "Кбит/с", "M": "Мбит/с", "G": "Гбит/с"}.get(unit, unit)
    return f"{num} {label}"


def traffic_reset_labels(msk_hour: int | None, gmt_offset: int | None) -> tuple[str, str]:
    """МСК и местное время сброса суточного трафика."""
    hour = int(msk_hour or 0) % 24
    msk = f"{hour:02d}:00 МСК"
    if gmt_offset is None:
        return msk, "—"
    local_h = (hour + int(gmt_offset)) % 24
    local = f"{local_h:02d}:00"
    gmt_lbl = f"GMT{int(gmt_offset):+d}" if gmt_offset != 0 else "GMT"
    return msk, f"{local} ({gmt_lbl})"


def tariff_display_name(
    is_juridical: int,
    service_meta: Optional[dict[str, Any]],
    sname_fallback: Optional[str] = None,
) -> str:
    """Название тарифа: для ЮЛ — Лимитный/Безлимитный по real_type, для ФЛ — service.name."""
    if is_juridical == 2:
        rt = (service_meta or {}).get("real_type")
        if rt == "default":
            return "Лимитный тариф"
        if rt:
            return "Безлимитный тариф"
    name = (service_meta or {}).get("name")
    if name:
        return str(name)
    return (sname_fallback or "").strip() or "—"


def jur_frozen_traffic_mb(
    remain: int | None, full_packet: int | None, jur_normal: int | None
) -> tuple[Optional[float], Optional[float]]:
    """
    Остаток основного пакета и использованный доп. трафик (МБ) для замороженного ЮЛ.
  remain — общий остаток (байты), full — полный пакет, jur_normal — основной пакет.
    """
    if remain is None or full_packet is None or jur_normal is None:
        return None, None
    remain_i, full_i, jur_i = int(remain), int(full_packet), int(jur_normal)
    dop_size = max(0, full_i - jur_i)
    if remain_i > dop_size:
        return bytes_to_mb(remain_i - dop_size), None
    dop_used = dop_size - remain_i
    return 0.0, bytes_to_mb(dop_used) if dop_used > 0 else None


def jur_traffic_overrun_mb(
    remain: int | None, full_packet: int | None, jur_normal: int | None
) -> Optional[float]:
    """Перерасход МБ, если основной пакет исчерпан (только ЮЛ + лимитный)."""
    if not jur_normal or not full_packet or remain is None:
        return None
    consumed = int(full_packet) - int(remain)
    if consumed > int(jur_normal):
        return bytes_to_mb(consumed - int(jur_normal))
    return None


def format_dt_msk(dt: datetime | None, *, time_sep: str = ", ", short_year: bool = False) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_MSK)
    if short_year:
        return local.strftime(f"%d.%m.%y{time_sep}%H:%M")
    return local.strftime(f"%d.%m.%Y{time_sep}%H:%M")


def format_money_ru(amount: float | None) -> str:
    """Сумма в ₽: тысячи через узкий пробел, без ,00 если целое."""
    if amount is None:
        return "—"
    value = round(float(amount), 2)
    if abs(value - round(value)) < 1e-9:
        body = f"{int(round(value)):,}".replace(",", "\u202f")
        return f"{body}\u202f₽"
    whole = int(value)
    kop = int(round((value - whole) * 100))
    body = f"{whole:,}".replace(",", "\u202f")
    return f"{body},{kop:02d}\u202f₽"


def format_dop_type_label(dop_name: Optional[str]) -> tuple[str, Optional[str]]:
    """Подпись типа для activated_dops; hint — полное имя для tooltip."""
    raw = (dop_name or "").strip()
    if not raw:
        return "Опция", None
    if raw.lower().startswith("увеличение"):
        m = re.search(r"на\s+(\d+)\s+дн", raw, re.IGNORECASE)
        if m:
            return f"Продление на {m.group(1)} дн.", raw
        tail = re.search(r"(на\s+\d+\s+дн(?:ей|я)?\.?)\s*$", raw, re.IGNORECASE)
        if tail:
            return f"Продление {tail.group(1).strip()}", raw
    return raw, raw


async def resolve_freeze_reason_label(
    session: AsyncSession, freeze: dict[str, Any]
) -> str:
    """Подпись причины заморозки: rus_reason из справочника, не код."""
    label = freeze.get("reason_short")
    if label:
        return str(label)

    from app.models.users import UserFreezeReasonCode

    code = freeze.get("reason_code")
    if code is None:
        raw = freeze.get("reason")
        if raw is not None and str(raw).strip().isdigit():
            code = int(str(raw).strip())

    if code is not None:
        r = await session.execute(
            select(UserFreezeReasonCode.rus_reason, UserFreezeReasonCode.short_reason).where(
                UserFreezeReasonCode.id == code
            )
        )
        row = r.one_or_none()
        if row and (row[0] or row[1]):
            return str(row[0] or row[1])

    raw = freeze.get("reason")
    return str(raw) if raw else "—"


def freeze_info_html(freeze: dict[str, Any], reason_label: str) -> str:
    """Краткий блок заморозки для быстрой проверки и подсказок."""
    df = format_dt_msk(freeze.get("date_freeze"), time_sep=" ")
    du = format_dt_msk(freeze.get("date_unfreeze"), time_sep=" ")
    lines = [
        '<div class="fc-freeze-info">',
        "<p><strong>Заморозка</strong> <span class=\"fc-freeze-tz\">(даты по МСК)</span></p>",
        "<ul>",
        f"<li><strong>Дата заморозки:</strong> {df or '—'}</li>",
    ]
    if du:
        lines.append(f"<li><strong>Дата разморозки:</strong> {du}</li>")
    lines.append(f"<li><strong>Причина:</strong> {reason_label}</li>")
    lines.append("</ul></div>")
    return "".join(lines)


def format_speed_display(speed: str) -> str:
    """Человекочитаемая скорость с префиксом «До»."""
    if not speed or speed.strip() in ("—", "-"):
        return "—"
    return f"До {speed}"


def format_valid_date_countdown(valid_date: datetime | None, *, now: datetime | None = None) -> str | None:
    """Сколько осталось до отключения тарифа по users.user_service_date.valid_date."""
    if not valid_date:
        return None
    ref = now or datetime.now(timezone.utc)
    end = valid_date if valid_date.tzinfo else valid_date.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    end = end.astimezone(timezone.utc)
    ref = ref.astimezone(timezone.utc)
    delta = end - ref
    total_sec = int(delta.total_seconds())
    if total_sec <= 0:
        return "срок действия истёк"
    days, rem = divmod(total_sec, 86400)
    hours = rem // 3600
    if days > 0:
        return f"через {days} дн. {hours} ч."
    if hours > 0:
        return f"через {hours} ч."
    mins = rem // 60
    return f"через {mins} мин."


def format_valid_date_remaining(valid_date: datetime | None, *, now: datetime | None = None) -> str | None:
    """Остаток срока тарифа: «осталось N дн HH:MM»."""
    if not valid_date:
        return None
    ref = now or datetime.now(timezone.utc)
    end = valid_date if valid_date.tzinfo else valid_date.replace(tzinfo=timezone.utc)
    end = end.astimezone(timezone.utc)
    ref = ref.astimezone(timezone.utc)
    total_sec = int((end - ref).total_seconds())
    if total_sec <= 0:
        return "срок действия истёк"
    days, rem = divmod(total_sec, 86400)
    hours = rem // 3600
    mins = (rem % 3600) // 60
    return f"осталось {days} дн {hours:02d}:{mins:02d}"


def coalesce_int(*values: int | None) -> int:
    for v in values:
        if v is not None:
            return int(v)
    return 0
