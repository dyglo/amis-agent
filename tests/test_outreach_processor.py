from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")

from amis_agent.application.services.outreach_processor import OutreachItem, process_outreach_items
from amis_agent.application.services.email import SuppressionStore


class DummySender:
    def __init__(self, fail_times: int = 0):
        self.sent = []
        self.fail_times = fail_times
        self.calls = 0

    def send(self, message):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("temp")
        self.sent.append(message)
        return {"id": "1"}


class DummySuppression(SuppressionStore):
    def __init__(self, blocked=None):
        self.blocked = set(blocked or [])

    def is_suppressed(self, email: str) -> bool:
        return email in self.blocked


class DummyLimiter:
    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0

    def can_send(self, ts, domain=None):
        return self.count < self.limit

    def record_send(self, ts, domain=None):
        self.count += 1


def test_outreach_processor_sends_when_allowed():
    sender = DummySender()
    store = DummySuppression()
    items = [
        OutreachItem(
            outreach_id=1,
            to_email="a@example.com",
            subject="Hi",
            body="Body",
            region="US",
            is_opt_in=False,
        )
    ]
    results = process_outreach_items(items, sender=sender, suppression_store=store)
    assert results[0].status == "sent"
    assert len(sender.sent) == 1


def test_outreach_processor_blocks_eu_without_opt_in():
    sender = DummySender()
    store = DummySuppression()
    items = [
        OutreachItem(
            outreach_id=2,
            to_email="b@example.com",
            subject="Hi",
            body="Body",
            region="EU",
            is_opt_in=False,
        )
    ]
    results = process_outreach_items(items, sender=sender, suppression_store=store)
    assert results[0].status == "blocked"
    assert len(sender.sent) == 0


def test_outreach_processor_blocks_suppressed():
    sender = DummySender()
    store = DummySuppression({"c@example.com"})
    items = [
        OutreachItem(
            outreach_id=3,
            to_email="c@example.com",
            subject="Hi",
            body="Body",
            region="US",
            is_opt_in=False,
        )
    ]
    results = process_outreach_items(items, sender=sender, suppression_store=store)
    assert results[0].status == "blocked"
    assert len(sender.sent) == 0


def test_outreach_processor_rate_limits():
    sender = DummySender()
    store = DummySuppression()
    limiter = DummyLimiter(limit=0)
    items = [
        OutreachItem(
            outreach_id=4,
            to_email="d@example.com",
            subject="Hi",
            body="Body",
            region="US",
            is_opt_in=False,
        )
    ]
    results = process_outreach_items(items, sender=sender, suppression_store=store, limit_store=limiter)
    assert results[0].status == "blocked"
    assert results[0].reason == "rate_limited"
    assert len(sender.sent) == 0


def test_outreach_processor_retries_then_succeeds():
    sender = DummySender(fail_times=2)
    store = DummySuppression()
    items = [
        OutreachItem(
            outreach_id=5,
            to_email="e@example.com",
            subject="Hi",
            body="Body",
            region="US",
            is_opt_in=False,
        )
    ]
    results = process_outreach_items(items, sender=sender, suppression_store=store)
    assert results[0].status == "sent"
    assert sender.calls == 3

