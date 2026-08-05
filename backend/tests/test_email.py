import httpx

from app.core.config import settings
from app.services.email import BREVO_EMAIL_URL, EmailService


def test_password_reset_uses_brevo_https_api(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return httpx.Response(201, request=httpx.Request("POST", url))

    monkeypatch.setattr(settings, "brevo_api_key", "test-key")
    monkeypatch.setattr(settings, "email_from", "no-reply@example.com")
    monkeypatch.setattr(settings, "email_from_name", "PromptForge AI")
    monkeypatch.setattr(settings, "frontend_url", "https://promptforge.example")
    monkeypatch.setattr("app.services.email.httpx.post", fake_post)

    assert EmailService().send_password_reset("user@example.com", "secret-token")
    assert captured["url"] == BREVO_EMAIL_URL
    assert captured["headers"] == {"api-key": "test-key"}
    assert captured["json"]["to"] == [{"email": "user@example.com"}]
    assert "secret-token" in captured["json"]["textContent"]
