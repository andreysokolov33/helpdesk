"""Обёртка Redis: при недоступности — no-op, запросы обслуживаются из БД."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, TypeVar

from redis.asyncio import Redis

logger = logging.getLogger("oss")

_OP_TIMEOUT = 0.5
_PING_TIMEOUT = 1.0

T = TypeVar("T")


class _NoOpPipeline:
    """Pipeline-заглушка: execute() бросает исключение → вызывающий код идёт в fallback."""

    async def __aenter__(self) -> "_NoOpPipeline":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def incr(self, key: str) -> None:
        pass

    async def expire(self, key: str, ttl: int, nx: bool = False) -> None:
        pass

    async def execute(self) -> list[Any]:
        raise ConnectionError("Redis unavailable")


class ResilientRedis:
    """Redis-клиент с кэшем доступности и короткими таймаутами."""

    def __init__(self, client: Redis, *, enabled: bool = True):
        self._client = client
        self._enabled = enabled
        self._available: Optional[bool] = None if enabled else False

    @property
    def available(self) -> bool:
        return self._enabled and self._available is not False

    def mark_unavailable(self) -> None:
        self._available = False

    def mark_available(self) -> None:
        self._available = True

    async def check_connection(self) -> bool:
        if not self._enabled:
            self._available = False
            return False
        try:
            await asyncio.wait_for(self._client.ping(), timeout=_PING_TIMEOUT)
            self._available = True
            return True
        except Exception as e:
            self._available = False
            logger.warning(
                "Redis unavailable: %s — cache disabled, requests will use DB",
                e,
            )
            return False

    async def ping(self) -> bool:
        return await self.check_connection()

    async def _run(self, op_name: str, factory: Callable[[], Awaitable[T]]) -> Optional[T]:
        if self._available is False:
            return None
        try:
            result = await asyncio.wait_for(factory(), timeout=_OP_TIMEOUT)
            if self._available is None:
                self._available = True
            return result
        except Exception as e:
            self._available = False
            logger.debug("Redis %s failed: %s", op_name, e)
            return None

    async def get(self, key: str) -> Optional[str]:
        return await self._run("GET", lambda: self._client.get(key))

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        if ex is not None:
            return await self._run("SET", lambda: self._client.set(key, value, ex=ex, **kwargs))
        return await self._run("SET", lambda: self._client.set(key, value, **kwargs))

    async def setex(self, key: str, ttl: int, value: str) -> Any:
        return await self._run("SETEX", lambda: self._client.setex(key, ttl, value))

    async def delete(self, *keys: str) -> Any:
        if self._available is False:
            return 0
        return await self._run("DELETE", lambda: self._client.delete(*keys))

    async def incr(self, key: str) -> Optional[int]:
        result = await self._run("INCR", lambda: self._client.incr(key))
        return int(result) if result is not None else None

    async def unlink(self, key: str) -> Any:
        return await self._run("UNLINK", lambda: self._client.unlink(key))

    async def flushdb(self) -> Any:
        return await self._run("FLUSHDB", lambda: self._client.flushdb())

    async def aclose(self) -> None:
        await self._client.aclose()

    def pipeline(self, transaction: bool = True) -> Any:
        if self._available is False:
            return _NoOpPipeline()
        return self._client.pipeline(transaction=transaction)

    async def scan_iter(self, match: Optional[str] = None, count: Optional[int] = None) -> AsyncIterator[str]:
        if self._available is False:
            if False:  # noqa: SIM114 — пустой async generator
                yield ""
            return
        try:
            kwargs: dict[str, Any] = {}
            if match is not None:
                kwargs["match"] = match
            if count is not None:
                kwargs["count"] = count
            async for key in self._client.scan_iter(**kwargs):
                if self._available is False:
                    break
                yield key
        except Exception as e:
            self._available = False
            logger.debug("Redis SCAN failed: %s", e)
