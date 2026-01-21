from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from amis_agent.infrastructure.scraping.http_client import HttpResponse, RateLimiter, fetch
from amis_agent.infrastructure.scraping.robots import RobotsCache


EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class EmailEvidence:
    email: str
    source_url: str
    confidence: int


@dataclass(frozen=True)
class EnrichmentResult:
    emails: list[EmailEvidence]
    personalization_line: str | None


Fetcher = Callable[[str, int], HttpResponse]


def extract_emails_from_html(html: str) -> set[str]:
    return {match.group(0).lower() for match in EMAIL_REGEX.finditer(html)}


def extract_mailto_emails(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    emails = set()
    for link in soup.select("a[href^='mailto:']"):
        href = link.get("href") or ""
        email = href.replace("mailto:", "").split("?")[0].strip().lower()
        if email:
            emails.add(email)
    return emails


def find_contact_links(html: str, base_url: str, *, limit: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(base_url).hostname or ""
    links: list[str] = []
    for link in soup.select("a[href]"):
        href = link.get("href") or ""
        if not href:
            continue
        if "contact" not in href.lower() and "about" not in href.lower():
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.hostname and parsed.hostname != host:
            continue
        if url not in links:
            links.append(url)
        if len(links) >= limit:
            break
    return links


class EmailEnricher:
    def __init__(
        self,
        *,
        fetcher: Fetcher | None = None,
        robots: RobotsCache | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.fetcher = fetcher or (lambda url, timeout: fetch(url, timeout_s=timeout))
        self.robots = robots or RobotsCache(cache={})
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cache: dict[str, str] = {}

    def _fetch_html(self, url: str, *, timeout_s: int, user_agent: str, max_requests: int, request_count: int) -> tuple[str | None, int]:
        if request_count >= max_requests:
            return None, request_count
        if not self.robots.get(url, user_agent).can_fetch(user_agent, url):
            return None, request_count
        if url in self.cache:
            return self.cache[url], request_count
        host = urlparse(url).hostname or ""
        self.rate_limiter.wait(host)
        resp = self.fetcher(url, timeout_s)
        if resp.status_code != 200:
            return None, request_count + 1
        self.cache[url] = resp.text
        return resp.text, request_count + 1

    def enrich(
        self,
        *,
        website_url: str,
        user_agent: str,
        timeout_s: int,
        max_contact_pages: int = 2,
        max_requests: int = 5,
    ) -> EnrichmentResult:
        request_count = 0
        homepage_html, request_count = self._fetch_html(
            website_url,
            timeout_s=timeout_s,
            user_agent=user_agent,
            max_requests=max_requests,
            request_count=request_count,
        )
        if not homepage_html:
            return EnrichmentResult([], None)

        personalization_line = extract_personalization_line(homepage_html)

        emails: dict[str, EmailEvidence] = {}
        for email in extract_mailto_emails(homepage_html):
            emails[email] = EmailEvidence(email=email, source_url=website_url, confidence=90)
        for email in extract_emails_from_html(homepage_html):
            emails.setdefault(email, EmailEvidence(email=email, source_url=website_url, confidence=70))

        contact_links = find_contact_links(homepage_html, website_url, limit=max_contact_pages)
        for link in contact_links:
            if request_count >= max_requests:
                break
            html, request_count = self._fetch_html(
                link,
                timeout_s=timeout_s,
                user_agent=user_agent,
                max_requests=max_requests,
                request_count=request_count,
            )
            if not html:
                continue
            if personalization_line is None:
                personalization_line = extract_personalization_line(html)
            for email in extract_mailto_emails(html):
                existing = emails.get(email)
                if not existing or existing.confidence < 90:
                    emails[email] = EmailEvidence(email=email, source_url=link, confidence=90)
            for email in extract_emails_from_html(html):
                emails.setdefault(email, EmailEvidence(email=email, source_url=link, confidence=70))
        return EnrichmentResult(list(emails.values()), personalization_line)


def extract_personalization_line(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(separator=" ").split())
    if not text:
        return None
    for sentence in text.split("."):
        cleaned = sentence.strip()
        if len(cleaned) >= 20:
            snippet = cleaned + "."
            return snippet[:512]
    return None
