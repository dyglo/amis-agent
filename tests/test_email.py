from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")

from amis_agent.application.services.email import (
    EmailMessage,
    SuppressionStore,
    append_footer,
    enforce_compliance,
    prepare_message,
)
from amis_agent.core.config import get_settings


class InMemorySuppressionStore(SuppressionStore):
    def __init__(self, suppressed: set[str] | None = None):
        self.suppressed = suppressed or set()

    def is_suppressed(self, email: str) -> bool:
        return email in self.suppressed


def test_append_footer_idempotent():
    body = "Hello"
    footer = "Footer"
    first = append_footer(body, footer)
    second = append_footer(first, footer)
    assert first == second


def test_prepare_message_adds_footer(monkeypatch):
    monkeypatch.setenv("FOOTER_TEXT", "")
    get_settings.cache_clear()
    msg = prepare_message("to@example.com", "Subject", "Body")
    assert isinstance(msg, EmailMessage)
    assert "Test User" in msg.body
    assert "TestCo" in msg.body
    assert "415 Mission St" in msg.body


def test_prepare_message_uses_footer_text_override(monkeypatch):
    monkeypatch.setenv("FOOTER_TEXT", "Custom Footer")
    get_settings.cache_clear()
    msg = prepare_message("to@example.com", "Subject", "Body")
    assert msg.body.endswith("Custom Footer")


def test_enforce_compliance_blocks_suppressed():
    store = InMemorySuppressionStore({"x@example.com"})
    try:
        enforce_compliance(
            to_email="x@example.com",
            region_code="US",
            is_opt_in=False,
            suppression_store=store,
        )
    except ValueError as exc:
        assert "suppressed" in str(exc)
    else:
        raise AssertionError("Expected suppression error")


def test_enforce_compliance_allows_us_auto_send():
    store = InMemorySuppressionStore()
    enforce_compliance(
        to_email="a@example.com",
        region_code="US",
        is_opt_in=False,
        suppression_store=store,
    )


def test_enforce_compliance_blocks_eu_without_opt_in():
    store = InMemorySuppressionStore()
    try:
        enforce_compliance(
            to_email="b@example.com",
            region_code="EU",
            is_opt_in=False,
            suppression_store=store,
        )
    except ValueError as exc:
        assert "opt_in" in str(exc)
    else:
        raise AssertionError("Expected opt-in error")

