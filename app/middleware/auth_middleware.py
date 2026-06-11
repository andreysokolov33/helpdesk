import logging
import json
import re
import http.cookies
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple

_TICKET_POLL_RE = re.compile(r"^/api/v1/helpdesk/tracker/(\d+)/poll$")

from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.datastructures import Headers
from fastapi import Response
# Твои импорты — проверь корректность путей
from app.core.auth_utils import (
    auth_cookie_options_from_scope,
    create_token,
    decode_jwt_token,
    _resolve_cookie_secure,
)
from app.api.v1.routers.auth.dao import (
    HelpdeskTokensDAO,
    SkystreamUserProjectAccessDAO,
    SkystreamUsersDAO,
)
from app.config import settings
from app.database import redis_client, async_session_maker

logger = logging.getLogger("auth_middleware")

_REDIS_KEY_SAFE_PREFIXES = ("helpdesk:grace_tokens:", "helpdesk:revoked_acc:", "operator:")


def _redis_key_log_label(key: str) -> str:
    for prefix in _REDIS_KEY_SAFE_PREFIXES:
        if key.startswith(prefix):
            return f"{prefix}***"
    if ":" in key:
        return key.split(":", 1)[0] + ":***"
    return "***"


class AuthMiddleware:
    def __init__(self, app: ASGIApp, login_path: str = "/login"):
        self.app = app
        self.login_path = login_path
        
        # Настройки путей (публичные auth-эндпоинты — только login/logout; /me проходит middleware)
        self.excluded_prefixes = {
            "/health", "/ready", "/static", "/media",
            "/login", "/openapi.json", "/favicon.ico",
            "/call_events", "/get_number_info", "/history_file_completed",
            "/api/v1/feedback",
        }
        self.excluded_exact_paths = {
            "/api/auth/login",
            "/api/auth/logout",
        }
        self.cacheable_paths = {
            "/api/v1/helpdesk/tickets/unread_count",
            "/api/v1/helpdesk/tracker/sidebar-counts",
            "/api/v1/statistics/analyze",
            "/api/v1/statistics/analyze/closed",
        }
        self.trusted_origins = settings.CORS_ORIGINS

    async def _redis_get(self, key: str) -> Optional[str]:
        try:
            return await redis_client.get(key)
        except Exception as e:
            logger.debug("Redis GET failed for %s: %s", _redis_key_log_label(key), e)
            return None

    async def _redis_set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            await redis_client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.debug("Redis SET failed for %s: %s", _redis_key_log_label(key), e)
            return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        headers = Headers(scope=scope)

        # 1. Быстрые исключения (White list)
        if self._is_excluded_path(path):
            await self.app(scope, receive, send)
            return

        cookies = self._parse_cookies(headers.get("cookie", ""))
        abs_acc_token = cookies.get("oss_acc_token")
        abs_ref_token = cookies.get("oss_ref_token")

        # 2. Проверка CSRF для небезопасных методов
        if scope["method"] not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            if not path.startswith("/api/"):
                if self._is_csrf_attack(headers):
                    res = Response(content=json.dumps({"detail": "CSRF failure"}), 
                                status_code=403, media_type="application/json")
                    await res(scope, receive, send)
                    return

        # 3. АУТЕНТИФИКАЦИЯ (Получаем данные и возможные новые куки)
        user_data, new_cookies = await self._authenticate(abs_acc_token, abs_ref_token)

        # 4. Создаем универсальный send_wrapper, который подмешает куки в ЛЮБОЙ ответ
        async def send_wrapper(message):
            if message["type"] == "http.response.start" and new_cookies:
                response_headers = list(message.get("headers", []))
                for name, data in new_cookies.items():
                    cookie_val = self._generate_cookie_header(
                        name, data["value"], data["expires"], scope
                    )
                    response_headers.append((b"set-cookie", cookie_val.encode("latin-1")))
                message["headers"] = response_headers
            await send(message)

        # 5. Если не авторизован (Редирект или 401)
        if not user_data:
            accept = headers.get("accept", "")
            if "text/html" in accept:
                res = Response(status_code=302, headers={"Location": self.login_path})
            else:
                res = Response(status_code=401, content=json.dumps({"detail": "Unauthorized"}))
            
            # ПРИНУДИТЕЛЬНАЯ ОЧИСТКА КУК ПРИ ОШИБКЕ
            cookie_opts = auth_cookie_options_from_scope(scope)
            res.delete_cookie("oss_acc_token", **cookie_opts)
            res.delete_cookie("oss_ref_token", **cookie_opts)
            res.delete_cookie("oss_login", **cookie_opts)
            
            await res(scope, receive, send)
            return

        # 6. Rate Limiting (ИСПРАВЛЕНО: передаем метод запроса)
        if not self._is_cacheable_path(path):
            # Передаем scope["method"] для разделения лимитов
            if await self._is_rate_limited(user_data["user_id"], scope["method"]):
                res = Response(
                    content=json.dumps({"detail": "Too many requests. Please slow down."}), 
                    status_code=429, 
                    media_type="application/json"
                )
                # Обязательно send_wrapper, чтобы не потерять обновленную сессию
                await res(scope, receive, send_wrapper) 
                return

        # 7. КЭШ ПОЛЛИНГА (только для путей, которые сами пишут в свой ключ)
        if self._is_cacheable_path(path):
            cache_key = self._cache_key_for_path(path, user_data["user_id"])
            if cache_key:
                cached_content = await self._redis_get(cache_key)
                if cached_content:
                    res = Response(content=cached_content, media_type="application/json")
                    await res(scope, receive, send_wrapper)
                    return

        # 8. Установка состояния запроса для Depends(get_current_user)
        scope["state"] = scope.get("state", {})
        scope["state"]["user"] = user_data

        # 9. Передача управления приложению
        await self.app(scope, receive, send_wrapper)

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ---

    def _is_excluded_path(self, path: str) -> bool:
        if path in self.excluded_exact_paths:
            return True
        return any(path.startswith(prefix) for prefix in self.excluded_prefixes)

    def _is_cacheable_path(self, path: str) -> bool:
        """Возвращает True для путей с серверным кэшем (rate-limit не применяется)."""
        if path in self.cacheable_paths:
            return True
        if _TICKET_POLL_RE.match(path):
            return True
        return False

    def _cache_key_for_path(self, path: str, user_id: int) -> Optional[str]:
        """Ключ Redis по path.

        Для poll-путей ключ общий (per-ticket), не per-user,
        чтобы N операторов на одном тикете читали один кэш.
        """
        if path == "/api/v1/helpdesk/tickets/unread_count":
            return f"unread_stats:{user_id}"
        m = _TICKET_POLL_RE.match(path)
        if m:
            return f"poll:ticket:{m.group(1)}"
        return None

    def _parse_cookies(self, cookie_str: str) -> Dict[str, str]:
        if not cookie_str: return {}
        try:
            c = http.cookies.SimpleCookie()
            c.load(cookie_str)
            return {k: v.value for k, v in c.items()}
        except Exception: return {}

    async def _authenticate(self, access: str, refresh: str) -> Tuple[Optional[dict], Optional[dict]]:
        """Логика проверки токенов."""
        # А. Проверяем Access
        if access:
            payload = await decode_jwt_token(access, token_type="access")
            # Если токен валиден (decode_jwt_token вернет None, если он протух)
            if payload:
                jti = payload.get("jti")
                # Быстрая проверка: отозванные access кэшируем в Redis (TTL = срок жизни access)
                if jti:
                    rev_key = f"helpdesk:revoked_acc:{jti}"
                    if await self._redis_get(rev_key):
                        pass  # отозван — пробуем refresh или 401
                    else:
                        async with async_session_maker() as db:
                            token_record = await HelpdeskTokensDAO.find_by_access_jti(db, jti)
                            if token_record and token_record.get("is_revoked"):
                                await self._redis_set(rev_key, "1", ex=max(60, settings.JWT_ACCESS_EXPIRE_MINUTES * 60))
                                pass
                            elif token_record:
                                user = await self._get_user_cached(payload["user_id"])
                                if user:
                                    return user, None

        # Б. Если Access протух, отозван или отсутствует — пробуем Refresh
        if refresh:
            return await self._handle_refresh_logic(refresh)

        return None, None

    async def _handle_refresh_logic(self, abs_ref_token: str) -> Tuple[Optional[dict], Optional[dict]]:
        """
        Ротация токенов с защитой от гонки запросов и логированием ошибок.
        """
        from uuid import UUID # Локальный импорт для безопасности типов

        async with async_session_maker() as db:
            try:
                # 1. Декодируем сам JWT
                payload = await decode_jwt_token(abs_ref_token, token_type="refresh")
                if not payload:
                    logger.warning("REFRESH: JWT signature invalid or expired")
                    return None, None

                jti = payload.get("jti")
                user_id = payload.get("user_id")

                # 2. Ищем запись в базе данных
                # ВАЖНО: Метод find_by_refresh_jti НЕ ДОЛЖЕН фильтровать по is_revoked!
                token_record = await HelpdeskTokensDAO.find_by_refresh_jti(db, jti)
                
                if not token_record:
                    logger.warning("REFRESH: Token record not found in database")
                    return None, None

                # 3. Проверяем существование и активность пользователя
                user = await SkystreamUsersDAO.find_one_or_none(db, id=user_id)
                if not user or not user.get("is_active"):
                    logger.warning(f"REFRESH: User {user_id} is inactive or does not exist")
                    return None, None

                if not await SkystreamUserProjectAccessDAO.user_can_login_helpdesk(db, int(user_id)):
                    logger.warning(f"REFRESH: User {user_id} has no helpdesk project access")
                    return None, None

                user_data = {
                    "user_id": user["id"],
                    "role": user.get("role"),
                    "level": user.get("level"),
                    "admin": user.get("is_superuser", False),
                    "full_name": user.get("full_name"),
                    "login": user.get("login"),
                }

                # 4. ОБРАБОТКА GRACE PERIOD (Если токен уже отозван параллельным запросом)
                if token_record.get("is_revoked"):
                    revoked_at = token_record.get("revoked_at")
                    if revoked_at:
                        if revoked_at.tzinfo is None:
                            revoked_at = revoked_at.replace(tzinfo=timezone.utc)
                        
                        diff = (datetime.now(timezone.utc) - revoked_at).total_seconds()
                        
                        # А. Grace Period: возвращаем кэшированные токены от первой вкладки
                        if diff < 60:
                            grace_key = f"helpdesk:grace_tokens:{jti}"
                            try:
                                cached = await self._redis_get(grace_key)
                                if cached:
                                    data = json.loads(cached)
                                    new_cookies = {}
                                    for name, kv in data.items():
                                        exp = datetime.fromisoformat(kv["expires"].replace("Z", "+00:00"))
                                        new_cookies[name] = {"value": kv["value"], "expires": exp}
                                    logger.debug(
                                        "REFRESH: Grace period (%ss), returning cached session",
                                        int(diff),
                                    )
                                    return user_data, new_cookies
                            except Exception as e:
                                logger.warning("REFRESH: Grace cache read failed: %s", e)
                            logger.debug(
                                "REFRESH: Grace period (%ss), no cached session",
                                int(diff),
                            )
                            return user_data, None
                        
                        # Б. Аварийное восстановление (если токен отозван давно, но браузер застрял)
                        # Проверяем, есть ли у пользователя НОВЫЕ активные сессии
                        latest_active = await HelpdeskTokensDAO.find_latest_active_session(db, user_id)
                        if latest_active and latest_active['refresh_jti'] != token_record['refresh_jti']:
                            # Если у пользователя уже есть более новая сессия, значит прошлая ротация 
                            # прошла успешно в БД, но не в браузере. 
                            # Мы НЕ можем вернуть старый токен, поэтому заставляем пользователя 
                            # перелогиниться, очистив всё (это сделает Шаг 5 в __call__).
                            logger.warning("REFRESH: Browser stuck with old session. Force logout.")
                            return None, None

                    return None, None
                # 5. ПРОВЕРКА ИСТЕЧЕНИЯ СРОКА В БАЗЕ (на случай, если JWT еще валиден, а БД говорит нет)
                exp_at = token_record.get("refresh_expires_at")
                if exp_at.tzinfo is None:
                    exp_at = exp_at.replace(tzinfo=timezone.utc)
                
                if exp_at < datetime.now(timezone.utc):
                    logger.warning("REFRESH: Token expired in database at %s", exp_at)
                    return None, None

                # 6. ГЕНЕРАЦИЯ НОВЫХ ТОКЕНОВ И РОТАЦИЯ
                new_access, exp_access, jti_access = await create_token(user, "access")
                new_refresh, exp_refresh, jti_refresh = await create_token(user, "refresh")

                # Атомарно обновляем токены в БД
                await HelpdeskTokensDAO.rotate_refresh(
                    db,
                    old_refresh_jti=jti,
                    new_access_jti=jti_access,
                    new_refresh_jti=jti_refresh,
                    access_expires_at=exp_access,
                    refresh_expires_at=exp_refresh,
                )
                
                await db.commit()

                # Формируем куки для установки в браузере
                new_cookies = {
                    "oss_acc_token": {"value": new_access, "expires": exp_access},
                    "oss_ref_token": {"value": new_refresh, "expires": exp_refresh},
                }
                # Кэш для Grace Period: параллельные вкладки получат токены без повторной ротации
                try:
                    cache_val = json.dumps({
                        k: {"value": v["value"], "expires": v["expires"].isoformat()}
                        for k, v in new_cookies.items()
                    })
                    await self._redis_set(f"helpdesk:grace_tokens:{jti}", cache_val, ex=60)
                except Exception as e:
                    logger.warning(f"REFRESH: Grace cache write failed: {e}")

                logger.info(f"REFRESH: Successful rotation for User {user_id}")
                return user_data, new_cookies

            except Exception as e:
                await db.rollback()
                logger.error(f"REFRESH: Unexpected failure: {e}", exc_info=True)
                return None, None

    async def _get_user_cached(self, user_id: int) -> Optional[dict]:
        cache_key = f"operator:{user_id}"
        try:
            async with async_session_maker() as db:
                if not await SkystreamUserProjectAccessDAO.user_can_login_helpdesk(db, user_id):
                    return None
                cached = await self._redis_get(cache_key)
                if cached:
                    return json.loads(cached)
                user = await SkystreamUsersDAO.find_one_or_none(db, id=user_id)
                if user and user.get("is_active"):
                    # ДОБАВЛЯЕМ fullname И ДРУГИЕ НУЖНЫЕ ПОЛЯ ЗДЕСЬ
                    data = {
                        "user_id": user["id"],
                        "role": user.get("role"),
                        "level": user.get("level"),
                        "admin": user.get("is_superuser", False),
                        "full_name": user.get("full_name"),
                        "login": user.get("login"),
                    }
                    await self._redis_set(cache_key, json.dumps(data), ex=600)
                    return data
        except Exception as e:
            logger.warning(f"User cache error: {e}")
        return None

    def _is_csrf_attack(self, headers: Headers) -> bool:
        origin = headers.get("origin") or headers.get("referer")
        if not origin: return True
        return not any(origin.startswith(t) for t in self.trusted_origins)

    async def _is_rate_limited(self, user_id: int, method: str) -> bool:
        """Раздельный лимит: GET — 600/мин, POST/и др. — 100/мин."""
        key = f"rl:{user_id}:{method}"
        limit = 600 if method == "GET" else 100
        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                await pipe.expire(key, 60, nx=True)
                res = await pipe.execute()
                return res[0] > limit
        except Exception:
            return False

    def _generate_cookie_header(self, name, value, expires, scope) -> str:
        """Сборка строки заголовка Set-Cookie."""
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        forwarded = headers.get("x-forwarded-proto") if settings.PROXY_HEADERS else None
        is_secure = _resolve_cookie_secure(
            scheme=scope.get("scheme"),
            forwarded_proto=forwarded,
        )
        
        # 1. Вычисляем Max-Age (разница в секундах между сейчас и временем истечения)
        now = datetime.now(timezone.utc)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        
        max_age = int((expires - now).total_seconds())
        if max_age < 0: max_age = 0 # Если токен уже протух
        
        # 2. Формируем заголовок. Используем И Max-Age И Expires для старых браузеров
        exp_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        header = (
            f"{name}={value}; "
            f"Max-Age={max_age}; "
            f"Expires={exp_str}; "
            f"Path=/; "
            f"HttpOnly; "
            f"SameSite=Lax"
        )
        if is_secure: header += "; Secure"
        return header