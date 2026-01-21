from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("GOOGLE_CREDENTIALS_FILE", "./secrets/gmail_credentials.json")
os.environ.setdefault("GOOGLE_TOKEN_FILE", "./secrets/gmail_token.json")
os.environ.setdefault("GOOGLE_SCOPES", "https://www.googleapis.com/auth/gmail.send")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")

from amis_agent.application.services.email import EmailMessage
from amis_agent.infrastructure.email.gmail_sender import GmailSender, _token_file_for_sender


def test_build_raw_message_contains_headers():
    message = EmailMessage(
        to_email="to@example.com",
        subject="Hello",
        body="Body",
        from_email="from@example.com",
        from_name="Tester",
    )
    raw = GmailSender.build_raw_message(message)
    assert raw


def test_token_file_per_sender():
    path = _token_file_for_sender("./secrets/gmail_token.json", "user@example.com")
    assert "user@example.com" in path


def test_sender_mismatch_raises():
    sender = GmailSender(
        credentials_file="x",
        token_file="y",
        scopes=[],
        expected_sender="right@example.com",
    )

    class FakeProfile:
        def execute(self):
            return {"emailAddress": "wrong@example.com"}

    class FakeUsers:
        def getProfile(self, userId: str):
            return FakeProfile()

    class FakeService:
        def users(self):
            return FakeUsers()

    try:
        sender._ensure_sender(FakeService())
    except ValueError as exc:
        assert "authenticated_sender_mismatch" in str(exc)
    else:
        raise AssertionError("Expected sender mismatch")

