from __future__ import annotations

from datetime import datetime, timezone

from amis_agent.core.config import get_settings
from amis_agent.infrastructure.queue.redis import get_redis_client


class SendHealthMonitor:
    def __init__(self, prefix: str = "send_errors"):
        self.prefix = prefix
        self.redis = get_redis_client()

    def _bucket(self, ts: datetime) -> str:
        return ts.replace(minute=0, second=0, microsecond=0).isoformat()

    def _key(self, ts: datetime) -> str:
        return f"{self.prefix}:{self._bucket(ts)}"

    def record_error(self, ts: datetime | None = None) -> int:
        now = ts or datetime.now(timezone.utc)
        key = self._key(now)
        value = self.redis.incr(key)
        if value == 1:
            # expire after 2 hours
            self.redis.expire(key, 7200)
        return int(value)

    def is_paused(self, ts: datetime | None = None) -> bool:
        settings = get_settings()
        now = ts or datetime.now(timezone.utc)
        key = self._key(now)
        value = int(self.redis.get(key) or 0)
        return value >= settings.send_error_spike_limit
