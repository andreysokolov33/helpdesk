import ipaddress
import logging
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("oss")


async def insert_into_operations(
    db: AsyncSession,
    operator: dict,
    user_id: int,
    operation_id: int,
    comment: Optional[str] = None,
    auto_commit: bool = True,
    *,
    amount: Optional[float] = None,
    balance_before: Optional[float] = None,
    balance_after: Optional[float] = None,
    record_date: Optional[int] = None,
) -> None:
    from app.utils.operations_log import insert_user_operation

    await insert_user_operation(
        db,
        operator=operator,
        target_user_id=user_id,
        id_type=operation_id,
        comment=comment or "",
        auto_commit=auto_commit,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        record_date=record_date,
    )


def get_client_ip(request: Request) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """
    Получение IP-адреса клиента из запроса.
    Проверяет X-Forwarded-For, X-Real-IP, Forwarded и client.host.
    """
    ip_str = None

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip_str = x_forwarded_for.split(",")[0].strip()

    if not ip_str:
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            ip_str = x_real_ip.strip()

    if not ip_str:
        forwarded = request.headers.get("forwarded")
        if forwarded:
            for_part = next(
                (p.strip() for p in forwarded.split(";") if p.strip().startswith("for=")),
                None,
            )
            if for_part:
                ip_str = for_part.split("=")[1].strip().strip("[]")

    if not ip_str:
        ip_str = request.client.host if request.client else None

    try:
        return ipaddress.ip_address(ip_str)
    except (ValueError, TypeError):
        return None
