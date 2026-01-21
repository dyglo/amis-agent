from __future__ import annotations

import redis

from amis_agent.core.config import get_settings


settings = get_settings()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)

