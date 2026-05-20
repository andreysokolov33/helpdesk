from datetime import date, datetime
from decimal import Decimal
from ipaddress import IPv4Address, IPv4Network
import json
import asyncio
import logging
from typing import Optional, Any
from app.database import redis_client

logger = logging.getLogger("abs")

class RedisCache:
    def __init__(self, prefix: str = "user"):
        self.redis = redis_client
        self.prefix = prefix

    def _get_key(self, key: Any) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: Any) -> Optional[dict]:
        try:
            data = await asyncio.wait_for(self.redis.get(self._get_key(key)), timeout=0.3)
            return json.loads(data) if data else None
        except Exception:
            logger.error("Redis GET error", exc_info=True)
            return None

    async def set(self, key: Any, value: dict, ttl: int = 3600 * 24):
        try:
            # Кастомный энкодер для сложных типов
            def default_converter(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, (Decimal, IPv4Address, IPv4Network)):
                    return str(obj)
                return str(obj)

            serialized_data = json.dumps(value, ensure_ascii=False, default=default_converter)
            await self.redis.set(self._get_key(key), serialized_data, ex=ttl)
        except Exception as e:
            logger.error(f"REDIS CACHE SET ERROR: {e}") # Не глотайте ошибки!

    async def patch(self, key: Any, updates: dict, ttl: int = 3600 * 24) -> bool:
        """Merge updates в существующий JSON; False если ключа нет."""
        cached = await self.get(key)
        if not cached:
            return False
        cached.update(updates)
        await self.set(key, cached, ttl=ttl)
        return True

    async def delete(self, key: Any):
        """Удалить один ключ."""
        try:
            await self.redis.delete(self._get_key(key))
        except Exception:
            logger.error("Redis DELETE error", exc_info=True)

    async def clear_prefix(self, pattern: Optional[str] = None):
        """
        Удаляет ключи по паттерну. 
        По умолчанию удаляет все ключи текущего префикса (например, 'user:*').
        """
        target_pattern = pattern or f"{self.prefix}:*"
        count = 0
        try:
            async for key in self.redis.scan_iter(match=target_pattern):
                await self.redis.unlink(key)
                count += 1
        except Exception:
            logger.error("Redis CLEAR_PREFIX error", exc_info=True)
        return count

    async def flush_all(self):
        """
        Полная очистка текущей базы данных Redis.
        Использовать с осторожностью.
        """
        try:
            await self.redis.flushdb()
        except Exception:
            logger.error("Redis FLUSHDB error", exc_info=True)