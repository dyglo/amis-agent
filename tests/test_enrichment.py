from __future__ import annotations

from dataclasses import dataclass

from amis_agent.application.services.enrichment import EmailEnricher


@dataclass(frozen=True)
class DummyResponse:
    url: str
    status_code: int
    text: str


class AllowAllRobots:
    def get(self, base_url: str, user_agent: str):
        class Parser:
            @staticmethod
            def can_fetch(_ua: str, _url: str) -> bool:
                return True

        return Parser()


class NoOpLimiter:
    def wait(self, host: str) -> None:
        return None


def test_enrichment_extracts_emails_from_contact_pages():
    homepage = "<a href='/contact'>Contact</a><a href='/about'>About</a>"
    contact = "Reach us at sales@example.com"
    about = "<a href='mailto:hello@example.com'>Email</a>"

    def fetcher(url: str, timeout: int):
        if url.endswith("/contact"):
            return DummyResponse(url=url, status_code=200, text=contact)
        if url.endswith("/about"):
            return DummyResponse(url=url, status_code=200, text=about)
        return DummyResponse(url=url, status_code=200, text=homepage)

    enricher = EmailEnricher(fetcher=fetcher, robots=AllowAllRobots(), rate_limiter=NoOpLimiter())
    result = enricher.enrich(
        website_url="https://example.com",
        user_agent="TestAgent",
        timeout_s=1,
        max_contact_pages=2,
        max_requests=5,
    )
    emails = {e.email for e in result.emails}
    assert "sales@example.com" in emails
    assert "hello@example.com" in emails
    assert result.personalization_line is not None
