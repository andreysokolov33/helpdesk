"""HTML-анкеты лидов «новое подключение» для поля tracker_tickets.body."""

from __future__ import annotations

import html
from typing import Literal

LeadKind = Literal["subscriber", "partner"]


def _row(label: str, value: str) -> str:
    return (
        f'<tr><th scope="row">{html.escape(label)}</th>'
        f"<td>{html.escape(value)}</td></tr>"
    )


def _yes_no(value: bool) -> str:
    return "Да" if value else "Нет"


def build_connection_lead_html(
    *,
    kind: LeadKind,
    full_name: str,
    address: str,
    phone: str,
    potential_subscribers: int | None = None,
    sees_network: bool | None = None,
    plans_new_station: bool | None = None,
    notes: str | None = None,
) -> str:
    """Компактная карточка-анкета (классы tk-lead*, стили в helpdesk-app.css)."""
    if kind == "subscriber":
        title = "Новое подключение — абонент"
        modifier = "subscriber"
        extra_row = _row("Видит сеть", _yes_no(bool(sees_network)))
    else:
        title = "Новое подключение — партнёр"
        modifier = "partner"
        extra_row = _row("Планирует новую станцию", _yes_no(bool(plans_new_station)))

    rows = [
        _row("ФИО", full_name.strip()),
        _row("Адрес", address.strip()),
        _row("Телефон", phone.strip()),
        extra_row,
    ]
    if kind == "partner" and potential_subscribers is not None:
        rows.append(_row("Потенциальных абонентов", str(int(potential_subscribers))))
    table = "".join(rows)
    notes_block = ""
    if (notes or "").strip():
        notes_block = (
            f'<p class="tk-lead__notes"><span class="tk-lead__notes-lbl">'
            f"Дополнительно</span>{html.escape(notes.strip())}</p>"
        )

    return (
        f'<div class="tk-lead tk-lead--{modifier}">'
        f'<p class="tk-lead__title">{html.escape(title)}</p>'
        f'<table class="tk-lead__table"><tbody>{table}</tbody></table>'
        f"{notes_block}</div>"
    )
