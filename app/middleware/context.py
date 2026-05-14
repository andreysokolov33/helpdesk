# app/middleware/context.py
from contextvars import ContextVar
from typing import Optional

# Текущий request_id для запроса
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

def get_request_id() -> Optional[str]:
    """Безопасно получить текущий request_id из контекста."""
    return request_id_ctx_var.get()

def set_request_id(value: Optional[str]) -> None:
    """Установить request_id в контекст (используется мидлварью)."""
    request_id_ctx_var.set(value)