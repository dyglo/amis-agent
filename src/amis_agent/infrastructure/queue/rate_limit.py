from __future__ import annotations

from datetime import datetime, timezone

from amis_agent.core.config import get_settings
from amis_agent.infrastructure.queue.redis import get_redis_client


class RedisLimitStore:
    def __init__(self, prefix: str = "send"):
        self.prefix = prefix
        self.redis = get_redis_client()

    def _key(self, ts: datetime, domain: str | None = None) -> str:
        suffix = ts.date().isoformat()
        if domain:
            return f"{self.prefix}:{domain}:{suffix}"
        return f"{self.prefix}:{suffix}"

    def get_count(self, ts: datetime, domain: str | None = None) -> int:
        value = self.redis.get(self._key(ts, domain))
        return int(value or 0)

    def increment(self, ts: datetime, domain: str | None = None) -> int:
        key = self._key(ts, domain)
        value = self.redis.incr(key)
        if value == 1:
            # expire after 2 days to keep keys bounded
            self.redis.expire(key, 172800)
        return int(value)


class RateLimiter:
    def __init__(self, store: RedisLimitStore | None = None):
        self.store = store or RedisLimitStore()

    def can_send(self, ts: datetime, domain: str | None = None) -> bool:
        settings = get_settings()
        if self.store.get_count(ts) >= settings.send_daily_limit:
            return False
        if domain:
            return self.store.get_count(ts, domain) < settings.send_domain_daily_limit
        return True

    def record_send(self, ts: datetime, domain: str | None = None) -> None:
        self.store.increment(ts)
        if domain:
            self.store.increment(ts, domain)

