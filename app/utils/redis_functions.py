import asyncio
import json
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional, Union
from functools import wraps
from redis.exceptions import ConnectionError, TimeoutError
from app.database import get_redis


logger = logging.getLogger("partner")

# Константы для блокировок
MAX_ATTEMPTS = 5
BLOCK_TIME = 300  # 5 минут


async def _redis_available(redis) -> bool:
    """Проверка доступности Redis без проброса исключений."""
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis недоступен: {e}")
        return False

def redis_safe(default_return=None):
    """Декоратор для безопасной работы с Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.error(f"Redis недоступен для {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"Ошибка в Redis операции {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

@redis_safe(default_return=None)
async def get_data_from_redis(id: Union[int, str], prefix: str) -> Optional[Union[dict, list]]:
    """
    Получить данные из Redis. Автоматически определяет тип ключа (hash или string).

    Args:
        id: Идентификатор сущности
        prefix: Префикс ключа

    Returns:
        dict или list, если данные найдены, иначе None
    """
    user_key = f"{prefix}:{id}"
    logger.debug(f'Start looking for {prefix.title()} with ID {id} in cache')

    async with get_redis() as redis:
        if not await _redis_available(redis):
            return None
        key_type = await redis.type(user_key)

        if key_type == "hash":
            data = await redis.hgetall(user_key)
            if data:
                logger.debug(f'Cache hit (hash) for {prefix.title()} with ID {id}')
                return data

        elif key_type == "string":
            raw = await redis.get(user_key)
            if raw:
                logger.debug(f'Cache hit (string) for {prefix.title()} with ID {id}')
                return json.loads(raw)

        logger.debug(f'Cache miss for {prefix.title()} with ID {id}')
        return None

@redis_safe()
async def save_in_redis(  
    data: Any,  
    prefix: str,
    id: str,  
    ttl: int = 3600  
) -> None:  
    """
    Универсальное сохранение информации в Redis.
    Поддерживает dict (как HSET) и сложные структуры (как JSON в SET).

    Args:
        data: Данные пользователя или произвольная структура
        prefix: Префикс ключа
        id: Идентификатор пользователя / объекта
        ttl: Время жизни кэша в секундах
    """
    redis_key = f"{prefix}:{id}"
    data_dict = None

    async with get_redis() as redis:
        if not await _redis_available(redis):
            return
        # Попробуем распознать dict-подобный объект
        if hasattr(data, "dict"):
            data_dict = data.dict()
        elif isinstance(data, dict):
            data_dict = data
        else:
            data_dict = None
        # Если data_dict подходит под HSET
        if data_dict and all(isinstance(k, str) for k in data_dict.keys()):
            hash_data = {}
            
            for k, v in data_dict.items():
                if isinstance(v, (dict, list)):
                    hash_data[k] = json.dumps(v, ensure_ascii=False)
                elif isinstance(v, (datetime, date)):
                    hash_data[k] = v.strftime("%Y-%m-%d %H:%M")
                elif v is None:
                    hash_data[k] = ''
                else:
                    hash_data[k] = str(v)

            await redis.hset(redis_key, mapping=hash_data)

        else:
            # Сохраняем сложный тип как JSON
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            await redis.set(redis_key, json_data)

        # TTL
        if ttl > 0:
            await redis.expire(redis_key, ttl)
        logger.debug(f"Add in cash for key={redis_key}")

@redis_safe(default_return=False)
async def update_data(  
    prefix: str,
    id: int,  
    fields_dict: Dict[str, Any]  
) -> bool:  
    """
    Обновление данных в Redis
    """
    try:  
        key = f'{prefix}:{id}'  
        logger.debug(f"Start update data with key {key}")
        
        async with get_redis() as redis:
            if not await _redis_available(redis):
                return False
            # Проверяем существование ключа  
            exists = await redis.exists(key)  
            if not exists:  
                logger.warning(f"Couldn't find data with key {key}")
                return False  

            # Преобразуем все значения в строки  
            update_dict = {}  
            for field, value in fields_dict.items():  
                if isinstance(value, (date, datetime)):  
                    update_dict[field] = value.isoformat()  
                elif value is None:  
                    update_dict[field] = ''  
                else:  
                    update_dict[field] = str(value)  
            
            # Обновляем поля  
            await redis.hset(key, mapping=update_dict)  
            logger.debug(f"New data {update_dict}")
            logger.info(f"Updated fields in cache for key {key}")
            return True  

    except Exception as e:  
        logger.exception(f"Couldn't update data in redis for key {key}") 
        return False

# Функции для блокировок
@redis_safe(default_return=False)
async def is_blocked(login: str) -> bool:
    """Проверяем, заблокирован ли пользователь"""
    async with get_redis() as redis:
        if not await _redis_available(redis):
            return False
        return await redis.exists(f"block:{login}") == 1

@redis_safe(default_return=None)
async def incr_failed_attempts(login: str):
    """Увеличиваем счетчик неудачных попыток"""
    async with get_redis() as redis:
        if not await _redis_available(redis):
            return None
        key = f"fail:{login}"
        attempts = await redis.incr(key)
        if attempts == 1:
            await redis.expire(key, BLOCK_TIME)

        if attempts >= MAX_ATTEMPTS:
            await redis.set(f"block:{login}", 1, ex=BLOCK_TIME)
            await redis.delete(key)
        return attempts

@redis_safe(default_return=None)
async def reset_failed_attempts(login: str):
    """Сбрасываем счетчик после успешной авторизации"""
    async with get_redis() as redis:
        if not await _redis_available(redis):
            return None
        await redis.delete(f"fail:{login}")
        await redis.delete(f"block:{login}")

@redis_safe(default_return=None)
async def get_block_time_left(login: str) -> Optional[str]:
    """Возвращает оставшееся время блокировки в формате ММ:СС"""
    async with get_redis() as redis:
        if not await _redis_available(redis):
            return None
        ttl = await redis.ttl(f"block:{login}")
        if ttl > 0:
            minutes, seconds = divmod(ttl, 60)
            return f"{minutes:02}:{seconds:02}"
        return None

# Вспомогательные функции
def run_async_task(async_func, *args, **kwargs):  
    """Wrapper для запуска асинхронных функций в BackgroundTasks"""  
    asyncio.create_task(async_func(*args, **kwargs))

async def _safe_save_in_redis(data, namespace, key):
    """Безопасное сохранение в Redis с таймаутом"""
    try:
        await asyncio.wait_for(save_in_redis(data, namespace, key), timeout=0.5)
    except Exception as e:
        logger.warning(f"Не удалось сохранить в Redis: {e}")
