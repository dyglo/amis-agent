from __future__ import annotations

from amis_agent.application.services.qualification import qualify_company, should_dedupe


def test_qualification_requires_name():
    decision = qualify_company(
        name="",
        website_status="has_website",
        website_url="https://example.com",
        region="US",
        source="source_a",
        allowed_sources=set(),
        allowed_domains=set(),
    )
    assert decision.allowed is False
    assert decision.reason == "missing_name"


def test_qualification_requires_website():
    decision = qualify_company(
        name="Acme",
        website_status="no_website",
        website_url=None,
        region="US",
        source="source_a",
        allowed_sources=set(),
        allowed_domains=set(),
    )
    assert decision.allowed is False
    assert decision.reason == "missing_website"


def test_qualification_enforces_allowlist():
    decision = qualify_company(
        name="Acme",
        website_status="has_website",
        website_url="https://example.com",
        region="US",
        source="source_a",
        allowed_sources={"source_b"},
        allowed_domains={"example.com"},
    )
    assert decision.allowed is False
    assert decision.reason == "source_not_allowed"


def test_qualification_allows_valid_company():
    decision = qualify_company(
        name="Acme",
        website_status="has_website",
        website_url="https://example.com",
        region="US",
        source="source_a",
        allowed_sources={"source_a"},
        allowed_domains={"example.com"},
    )
    assert decision.allowed is True
    assert decision.score > 0


def test_dedupe_by_name_and_domain():
    existing = {("acme co", "example.com")}
    assert should_dedupe("Acme Co", "example.com", existing) is True
