# app/core/context.py
from contextvars import ContextVar
from typing import Optional

# Request ID для трейсинга запросов
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

# Опционально: user_id для аудита
user_id_ctx_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)