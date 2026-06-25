"""Контакты менеджеров (role=manager) для подстановки в статьях БЗ и fast-check."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.fast_check_schemas import ManagerContact

_LEGACY_PHONE = "89588616731"
_LEGACY_EMAIL = "cm@wifitochka.ru"

_PLACEHOLDER_PHONE = "{{manager_phone}}"
_PLACEHOLDER_PHONES = "{{manager_phones}}"
_PLACEHOLDER_EMAIL = "{{manager_email}}"
_PLACEHOLDER_EMAILS = "{{manager_emails}}"

_MAX_PHONES = 2
_MAX_EMAILS = 2


async def load_manager_contacts(session: AsyncSession) -> list[ManagerContact]:
    """Активные пользователи с role=manager и их телефоны/почты."""
    try:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT su.id, su.full_name
                    FROM users.skystream_users su
                    WHERE su.role = 'manager' AND su.is_active IS TRUE
                    ORDER BY su.full_name NULLS LAST, su.id
                    LIMIT 20
                    """
                )
            )
        ).mappings().all()

        managers: list[ManagerContact] = []
        for row in rows:
            mid = int(row["id"])
            phones = (
                await session.execute(
                    text(
                        """
                        SELECT phone FROM users.skystream_user_phones
                        WHERE user_id = :mid
                        ORDER BY is_primary DESC NULLS LAST, id
                        """
                    ),
                    {"mid": mid},
                )
            ).scalars().all()
            emails = (
                await session.execute(
                    text(
                        """
                        SELECT email FROM users.skystream_user_emails
                        WHERE user_id = :mid
                        ORDER BY is_primary DESC NULLS LAST, id
                        """
                    ),
                    {"mid": mid},
                )
            ).scalars().all()
            managers.append(
                ManagerContact(
                    full_name=(row["full_name"] or "").strip() or None,
                    phones=[str(p).strip() for p in phones if p and str(p).strip()],
                    emails=[str(e).strip() for e in emails if e and str(e).strip()],
                )
            )
        return [m for m in managers if m.phones or m.emails]
    except Exception:
        return []


def collect_manager_phones_emails(
    managers: list[ManagerContact],
    *,
    max_phones: int = _MAX_PHONES,
    max_emails: int = _MAX_EMAILS,
) -> tuple[list[str], list[str]]:
    phones: list[str] = []
    emails: list[str] = []

    for manager in managers:
        for phone in manager.phones:
            if phone not in phones:
                phones.append(phone)
            if len(phones) >= max_phones:
                break
        if len(phones) >= max_phones:
            break

    for manager in managers:
        for email in manager.emails:
            low = email.lower()
            if not any(e.lower() == low for e in emails):
                emails.append(email)
            if len(emails) >= max_emails:
                break
        if len(emails) >= max_emails:
            break

    return phones, emails


def _join_contacts(items: list[str], *, empty: str = "—") -> str:
    return ", ".join(items) if items else empty


def substitute_manager_contacts(
    text: str | None,
    *,
    phones: list[str],
    emails: list[str],
) -> str | None:
    """Подстановка плейсхолдеров и устаревших захардкоженных контактов."""
    if text is None:
        return None
    if not text:
        return text

    phone_display = _join_contacts(phones)
    email_display = _join_contacts(emails)
    phone_first = phones[0] if phones else "—"
    email_first = emails[0] if emails else "—"

    replacements: list[tuple[str, str]] = [
        (_PLACEHOLDER_PHONES, phone_display),
        (_PLACEHOLDER_PHONE, phone_first),
        (_PLACEHOLDER_EMAILS, email_display),
        (_PLACEHOLDER_EMAIL, email_first),
        ("{{kb_manager_phones}}", phone_display),
        ("{{kb_manager_phone}}", phone_first),
        ("{{kb_manager_emails}}", email_display),
        ("{{kb_manager_email}}", email_first),
        (_LEGACY_PHONE, phone_display if len(phones) > 1 else phone_first),
        (_LEGACY_EMAIL, email_display if len(emails) > 1 else email_first),
    ]

    result = text
    for old, new in replacements:
        if old in result:
            result = result.replace(old, new)
    return result


async def load_manager_contact_lists(session: AsyncSession) -> tuple[list[str], list[str]]:
    managers = await load_manager_contacts(session)
    return collect_manager_phones_emails(managers)


def apply_contacts_to_quiz_questions(
    questions: list[dict[str, Any]],
    *,
    phones: list[str],
    emails: list[str],
) -> list[dict[str, Any]]:
    for question in questions:
        question["question_text"] = substitute_manager_contacts(
            str(question.get("question_text") or ""),
            phones=phones,
            emails=emails,
        )
        for option in question.get("options") or []:
            option["option_text"] = substitute_manager_contacts(
                str(option.get("option_text") or ""),
                phones=phones,
                emails=emails,
            )
    return questions
