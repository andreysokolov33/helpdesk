"""Отправка писем через SMTP SkyStream (переменные SMTP_*_SKYSTREAM)."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional, Sequence, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

Attachment = Tuple[bytes, str, str, str]  # data, maintype, subtype, filename


def smtp_skystream_is_configured() -> bool:
    return bool(
        settings.SMTP_HOST_SKYSTREAM
        and str(settings.SMTP_HOST_SKYSTREAM).strip()
        and settings.SMTP_USER_SKYSTREAM
        and str(settings.SMTP_USER_SKYSTREAM).strip()
        and settings.SMTP_PASSWORD_SKYSTREAM is not None
        and str(settings.SMTP_PASSWORD_SKYSTREAM).strip()
        and settings.SMTP_FROM_EMAIL_SKYSTREAM
        and str(settings.SMTP_FROM_EMAIL_SKYSTREAM).strip()
    )


def send_skystream_email(
    *,
    to_addr: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[Sequence[Attachment]] = None,
) -> None:
    if not smtp_skystream_is_configured():
        raise RuntimeError(
            "SMTP SkyStream не настроен: задайте SMTP_HOST_SKYSTREAM, SMTP_USER_SKYSTREAM, "
            "SMTP_PASSWORD_SKYSTREAM, SMTP_FROM_EMAIL_SKYSTREAM"
        )

    from_email = str(settings.SMTP_FROM_EMAIL_SKYSTREAM).strip()
    from_name = (settings.SMTP_FROM_NAME_SKYSTREAM or "WiFiТочка").strip()

    for name, val in (("Subject", subject), ("To", to_addr), ("From", from_email)):
        if val and any(ch in str(val) for ch in ("\r", "\n")):
            raise ValueError(f"Недопустимые символы в заголовке {name}")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = to_addr
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    for data, maintype, subtype, filename in attachments or ():
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    host = str(settings.SMTP_HOST_SKYSTREAM).strip()
    port = int(settings.SMTP_PORT_SKYSTREAM or 465)
    user = str(settings.SMTP_USER_SKYSTREAM).strip()
    password = str(settings.SMTP_PASSWORD_SKYSTREAM or "")
    ctx = ssl.create_default_context()

    if settings.SMTP_USE_SSL_SKYSTREAM or port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=120) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=120) as smtp:
            smtp.ehlo()
            if settings.SMTP_STARTTLS_SKYSTREAM:
                smtp.starttls(context=ctx)
                smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg)

    logger.info("SMTP SkyStream: письмо отправлено на %s", to_addr)
