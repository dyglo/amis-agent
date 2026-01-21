from __future__ import annotations

from urllib.parse import urlparse

from amis_agent.core.config import get_settings
from amis_agent.infrastructure.scraping.http_client import ensure_allowed_domain


def test_ensure_allowed_domain_allows_when_empty(monkeypatch):
    monkeypatch.setenv("SCRAPE_ALLOWED_DOMAINS", "")
    get_settings.cache_clear()
    ensure_allowed_domain("https://anydomain.test/path")


def test_ensure_allowed_domain_blocks_disallowed(monkeypatch):
    monkeypatch.setenv("SCRAPE_ALLOWED_DOMAINS", "allowed.com")
    get_settings.cache_clear()
    try:
        ensure_allowed_domain("https://blocked.com/x")
    except ValueError as exc:
        assert "domain_not_allowed" in str(exc)
    else:
        raise AssertionError("Expected domain_not_allowed")

