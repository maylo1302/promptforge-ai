import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Wysyła e-maile przez skonfigurowany SMTP; lokalnie nie ujawnia tokenów w logach."""

    def send_password_reset(self, recipient: str, token: str) -> bool:
        if not settings.smtp_host:
            logger.warning("SMTP nie jest skonfigurowany — e-mail odzyskiwania nie został wysłany.")
            return False
        reset_url = f"{settings.frontend_url.rstrip('/')}/odzyskaj-haslo?{urlencode({'token': token})}"
        message = EmailMessage()
        message["Subject"] = "PromptForge AI — odzyskanie hasła"
        message["From"] = settings.email_from
        message["To"] = recipient
        message.set_content(f"""Cześć,

otrzymaliśmy prośbę o zmianę hasła do PromptForge AI.

Ustaw nowe hasło, korzystając z linku ważnego przez 30 minut:
{reset_url}

Jeżeli to nie Ty wysłałeś prośbę, zignoruj tę wiadomość.
""")
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            return True
        except (OSError, smtplib.SMTPException):
            logger.exception("Nie udało się wysłać e-maila odzyskiwania hasła.")
            return False


email_service = EmailService()
