import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    """Sends password-reset emails through Brevo's HTTPS API or SMTP locally."""

    def send_password_reset(self, recipient: str, token: str) -> bool:
        reset_url = f"{settings.frontend_url.rstrip('/')}/odzyskaj-haslo?{urlencode({'token': token})}"
        subject = "PromptForge AI — odzyskanie hasła"
        text = f"""Cześć,

otrzymaliśmy prośbę o zmianę hasła do PromptForge AI.

Ustaw nowe hasło, korzystając z linku ważnego przez 30 minut:
{reset_url}

Jeżeli to nie Ty wysłałeś prośbę, zignoruj tę wiadomość.
"""

        if settings.brevo_api_key:
            return self._send_with_brevo(recipient, subject, text)
        if settings.smtp_host:
            return self._send_with_smtp(recipient, subject, text)
        logger.warning("E-mail odzyskiwania nie jest skonfigurowany.")
        return False

    @staticmethod
    def _send_with_brevo(recipient: str, subject: str, text: str) -> bool:
        try:
            response = httpx.post(
                BREVO_EMAIL_URL,
                headers={"api-key": settings.brevo_api_key},
                json={
                    "sender": {"name": settings.email_from_name, "email": settings.email_from},
                    "to": [{"email": recipient}],
                    "subject": subject,
                    "textContent": text,
                },
                timeout=15,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            logger.exception("Nie udało się wysłać e-maila odzyskiwania przez Brevo.")
            return False

    @staticmethod
    def _send_with_smtp(recipient: str, subject: str, text: str) -> bool:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email_from
        message["To"] = recipient
        message.set_content(text)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            return True
        except (OSError, smtplib.SMTPException):
            logger.exception("Nie udało się wysłać e-maila odzyskiwania przez SMTP.")
            return False


email_service = EmailService()
