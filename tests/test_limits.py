from __future__ import annotations

from amis_agent.application.services.limits import can_send_today, daily_bucket_key


def test_can_send_today():
    assert can_send_today(0, daily_limit=5)
    assert can_send_today(4, daily_limit=5)
    assert not can_send_today(5, daily_limit=5)


def test_daily_bucket_key():
    key = daily_bucket_key("send")
    assert key.startswith("send:")

