from __future__ import annotations

from datetime import datetime, timezone

from amis_agent.infrastructure.queue.rate_limit import RateLimiter


class FakeStore:
    def __init__(self, counts: dict[str, int]):
        self.counts = counts

    def get_count(self, ts: datetime, domain: str | None = None) -> int:
        key = f"{domain or 'all'}:{ts.date().isoformat()}"
        return self.counts.get(key, 0)

    def increment(self, ts: datetime, domain: str | None = None) -> int:
        key = f"{domain or 'all'}:{ts.date().isoformat()}"
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]


def test_rate_limiter_blocks_by_domain(monkeypatch):
    monkeypatch.setenv("SEND_DAILY_LIMIT", "10")
    monkeypatch.setenv("SEND_DOMAIN_DAILY_LIMIT", "2")
    store = FakeStore({f"example.com:{datetime.now(timezone.utc).date().isoformat()}": 2})
    limiter = RateLimiter(store=store)
    assert limiter.can_send(datetime.now(timezone.utc), "example.com") is False
