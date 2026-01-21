from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "from@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Tester")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("GOOGLE_CREDENTIALS_FILE", "./secrets/gmail_credentials.json")
os.environ.setdefault("GOOGLE_TOKEN_FILE", "./secrets/gmail_token.json")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")

from scripts.send_real_email import send_real_email


class DummySender:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)
        return {"id": "1"}


def test_send_real_email_uses_sender(monkeypatch):
    dummy = DummySender()

    def fake_from_settings():
        return dummy

    monkeypatch.setattr("scripts.send_real_email.from_settings", fake_from_settings)

    result = send_real_email("to@example.com", "Hello", "Body")
    assert result.status == "sent"
    assert len(dummy.sent) == 1

