"""Перевод сообщений Pydantic/FastAPI 422 на русский для ответов API."""

from __future__ import annotations

from typing import Any, Dict, List

# Точные совпадения англ. текста (разные версии Pydantic)
_EN_FALLBACK: Dict[str, str] = {
    "Field required": "Обязательное поле",
    "none is not an allowed value": "Укажите значение",
    "Input should be a valid integer": "Укажите целое число",
    "Input should be a valid number": "Укажите число",
    "Input should be a valid string": "Укажите строку",
    "Input should be a valid boolean": "Укажите да или нет",
    "Internal Server Error": "Внутренняя ошибка сервера",
}


def validation_error_msg_ru(err: Dict[str, Any]) -> str:
    """Сообщение для одного элемента из exc.errors()."""
    t = err.get("type", "")
    ctx = err.get("ctx") or {}
    raw_msg = (err.get("msg") or "").strip()

    if t == "string_too_short":
        min_len = ctx.get("min_length", 0)
        if min_len >= 1:
            return "Поле не должно быть пустым"
        return f"Минимум {min_len} символов"

    if t == "string_too_long":
        max_len = ctx.get("max_length", "")
        loc = err.get("loc") or ()
        loc_tail = loc[-1] if loc else None
        if loc_tail == "q" and len(loc) >= 2 and loc[0] == "query":
            return (
                f"Текст в поле поиска слишком длинный. Допустимо не более {max_len} символов."
            )
        return f"Значение слишком длинное. Допустимо не более {max_len} символов."

    if t in ("missing", "value_error.missing"):
        return "Обязательное поле"

    if t == "greater_than":
        gt = ctx.get("gt")
        if gt is not None:
            return f"Значение должно быть больше {gt}"
        return "Слишком маленькое значение"

    if t == "greater_than_equal":
        ge = ctx.get("ge")
        if ge is not None:
            return f"Значение должно быть не меньше {ge}"
        return "Слишком маленькое значение"

    if t == "less_than":
        lt = ctx.get("lt")
        if lt is not None:
            return f"Значение должно быть меньше {lt}"
        return "Слишком большое значение"

    if t == "less_than_equal":
        le = ctx.get("le")
        if le is not None:
            return f"Значение должно быть не больше {le}"
        return "Слишком большое значение"

    if t in ("int_parsing", "float_parsing", "decimal_parsing"):
        return "Укажите корректное число"

    if t == "bool_parsing":
        return "Укажите логическое значение"

    if t == "value_error":
        # Кастомные ValueError из валидаторов — часто уже по-русски
        if raw_msg and _looks_russian(raw_msg):
            return raw_msg

    if t and t.startswith("value_error"):
        if raw_msg and _looks_russian(raw_msg):
            return raw_msg

    if raw_msg in _EN_FALLBACK:
        return _EN_FALLBACK[raw_msg]

    # Частые шаблоны англ. строк (Pydantic v2)
    if "at least" in raw_msg.lower() and "character" in raw_msg.lower():
        return "Поле не должно быть пустым"
    if "at most" in raw_msg.lower() and "character" in raw_msg.lower():
        return "Слишком длинное значение"

    if raw_msg and _looks_russian(raw_msg):
        return raw_msg

    return raw_msg or "Ошибка проверки данных"


def _looks_russian(s: str) -> bool:
    return any("\u0400" <= c <= "\u04ff" for c in s)


_SAFE_CTX_KEYS = frozenset(
    {"max_length", "min_length", "gt", "ge", "lt", "le", "multiple_of"}
)


def localize_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Список ошибок: msg по-русски, без поля input (не утечёт длинный/чужой текст в ответ API)."""
    out: List[Dict[str, Any]] = []
    for err in errors:
        msg = validation_error_msg_ru(err)
        loc = err.get("loc")
        e: Dict[str, Any] = {
            "loc": list(loc) if isinstance(loc, (list, tuple)) else loc,
            "msg": msg,
            "type": err.get("type"),
        }
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and ctx:
            safe_ctx = {k: v for k, v in ctx.items() if k in _SAFE_CTX_KEYS}
            if safe_ctx:
                e["ctx"] = safe_ctx
        out.append(e)
    return out
