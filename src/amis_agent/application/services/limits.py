from __future__ import annotations

from datetime import date

from amis_agent.core.config import get_settings


def can_send_today(sent_today: int, daily_limit: int | None = None) -> bool:
    settings = get_settings()
    limit = daily_limit if daily_limit is not None else settings.send_daily_limit
    return sent_today < limit


def daily_bucket_key(prefix: str = "send") -> str:
    return f"{prefix}:{date.today().isoformat()}"

