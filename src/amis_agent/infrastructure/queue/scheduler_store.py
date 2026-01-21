from __future__ import annotations

from datetime import datetime

from amis_agent.infrastructure.queue.redis import get_redis_client


class SchedulerStore:
    def __init__(self, prefix: str = "scheduler"):
        self.prefix = prefix
        self.redis = get_redis_client()

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    def get_last_run(self, name: str) -> datetime | None:
        value = self.redis.get(self._key(name))
        if not value:
            return None
        return datetime.fromisoformat(value)

    def set_last_run(self, name: str, ts: datetime) -> None:
        self.redis.set(self._key(name), ts.isoformat())

