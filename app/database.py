# app/database.py
from contextlib import asynccontextmanager
import logging
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
from app.core.redis_resilience import ResilientRedis
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from typing import AsyncGenerator

logger = logging.getLogger("oss")

DatabaseSession = AsyncGenerator[AsyncSession, None]

# ── Параметры пула в зависимости от режима ──
if settings.MODE == "TEST":
    DATABASE_URL = settings.DATABASE_URL
    DATABASE_PARAMS = {"poolclass": NullPool}
else:
    DATABASE_URL = settings.DATABASE_URL
    DATABASE_PARAMS = {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
    }

# ── Движок ──
engine = create_async_engine(DATABASE_URL, **DATABASE_PARAMS)

# ── Сессия ──
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Базовый класс для моделей ──
class Base(DeclarativeBase):
    pass

# ── Redis (при недоступности — no-op, запросы идут в БД) ──
_redis_kw: dict = {
    "host": settings.REDIS_HOST,
    "port": settings.REDIS_PORT,
    "db": settings.REDIS_DB,
    "decode_responses": True,
    "socket_timeout": 0.5,
    "socket_connect_timeout": 0.3,
    "retry": Retry(NoBackoff(), 0),
    "health_check_interval": 0,
    "max_connections": 200,
}
if settings.REDIS_PASSWORD:
    _redis_kw["password"] = settings.REDIS_PASSWORD

_redis_raw = Redis(**_redis_kw)
redis_client = ResilientRedis(_redis_raw, enabled=settings.REDIS_ENABLED)


@asynccontextmanager
async def get_redis():
    try:
        yield redis_client
    finally:
        pass  # Клиент закрывается один раз при завершении приложения


async def get_db() -> DatabaseSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def background_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Для фоновых задач (Celery, BackgroundTasks) — сами управляют транзакцией."""
    session: AsyncSession = async_session_maker()
    try:
        yield session
    except Exception:
        await session.rollback()
        logger.error("Database error in background task", exc_info=True)
        raise
    finally:
        await session.close()
        logger.debug("Background DB session closed")


@asynccontextmanager
async def request_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Для middleware — когда нет доступа к Depends(get_db)."""
    session: AsyncSession = async_session_maker()
    try:
        yield session
    except Exception:
        await session.rollback()
        logger.error("DB error in middleware", exc_info=True)
        raise
    finally:
        await session.close()


__all__ = (
    "Base",
    "engine",
    "async_session_maker",
    "get_db",
    "get_redis",
    "redis_client",
    "background_db_session",
    "request_db_session",
)
