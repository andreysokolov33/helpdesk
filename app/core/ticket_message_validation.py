"""Валидация текста ответа оператора в чате тикета."""

from __future__ import annotations

import re
from html import unescape

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_DOTS_ONLY_RE = re.compile(r"^[\s.\u2026…·]+$", re.UNICODE)

_BRIEF_RESPONSES = frozenset(
    {
        "ok",
        "ок",
        "okay",
        "окей",
        "k",
        "да",
        "нет",
        "ага",
        "угу",
        "ну",
        "хм",
        "hm",
        "mmm",
        "ммм",
        "yes",
        "no",
        "yep",
        "nope",
        "ya",
        "неа",
        "спс",
        "thx",
        "пон",
        "понял",
        "ясно",
        "принял",
        "ладно",
        "норм",
        "norm",
        "clear",
        "done",
        "готово",
        "++",
        "+",
    }
)

_VALIDATION_MESSAGES = {
    "empty": "Нельзя отправить пустое сообщение. Добавьте текст, изображение или файл.",
    "dots_only": "Нельзя отправить сообщение из одних точек.",
    "punctuation_only": "Сообщение должно содержать слова, а не только знаки препинания.",
    "too_brief": "Пожалуйста, используйте более развёрнутые ответы — клиенту нужна понятная информация.",
}


def html_to_plain_text(html: str) -> str:
    if not (html or "").strip():
        return ""
    text = re.sub(r"<br\s*/?>", " ", html, flags=re.I)
    text = re.sub(r"</p>", " ", text, flags=re.I)
    text = _HTML_TAG_RE.sub("", text)
    text = unescape(text).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _has_letter(text: str) -> bool:
    return any(ch.isalpha() for ch in text)


def _is_single_short_word(word: str) -> bool:
    return 1 <= len(word) <= 3 and word.isalpha()


def _normalize_for_brief_check(text: str) -> str:
    normalized = re.sub(r"[\s.,!?…:;—–\-'\"«»()\[\]{}]+", " ", text.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _is_too_brief(plain: str) -> bool:
    normalized = _normalize_for_brief_check(plain)
    if not normalized:
        return False
    if normalized in _BRIEF_RESPONSES:
        return True
    words = [w for w in normalized.split() if w]
    return len(words) == 1 and _is_single_short_word(words[0])


def validate_ticket_message_text(text: str, *, has_attachments: bool) -> str | None:
    """Возвращает текст ошибки или None, если сообщение допустимо."""
    plain = html_to_plain_text(text)

    if not plain:
        if has_attachments:
            return None
        return _VALIDATION_MESSAGES["empty"]

    if _DOTS_ONLY_RE.fullmatch(plain):
        return _VALIDATION_MESSAGES["dots_only"]

    if not _has_letter(plain):
        return _VALIDATION_MESSAGES["punctuation_only"]

    if _is_too_brief(plain):
        return _VALIDATION_MESSAGES["too_brief"]

    return None
