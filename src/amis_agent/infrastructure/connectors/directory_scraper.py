from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from amis_agent.application.services.discovery import BusinessListing
from amis_agent.core.config import get_settings
from amis_agent.infrastructure.scraping.http_client import HttpResponse, RateLimiter, ensure_allowed_domain, fetch
from amis_agent.infrastructure.scraping.robots import RobotsCache


Fetcher = Callable[[str, int], HttpResponse]


@dataclass(frozen=True)
class DirectoryScrapeConfig:
    base_url: str
    listing_selector: str
    name_selector: str
    website_selector: str | None
    region: str
    source: str


class GenericDirectoryConnector:
    def __init__(
        self,
        config: DirectoryScrapeConfig,
        fetcher: Fetcher | None = None,
        *,
        check_robots: bool = True,
    ):
        self.config = config
        self.fetcher = fetcher or (lambda url, timeout: fetch(url, timeout_s=timeout))
        self.rate_limiter = RateLimiter()
        self.robots = RobotsCache(cache={})
        self.check_robots = check_robots

    def fetch(self, *, region: str, limit: int) -> list[BusinessListing]:
        if region != self.config.region:
            return []
        ensure_allowed_domain(self.config.base_url)
        host = urlparse(self.config.base_url).hostname or ""
        self.rate_limiter.wait(host)

        if self.check_robots:
            user_agent = get_settings().scrape_user_agent
            parser = self.robots.get(self.config.base_url, user_agent)
            if not parser.can_fetch(user_agent, self.config.base_url):
                return []

        resp = self.fetcher(self.config.base_url, get_settings().scrape_timeout_s)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        listings = []
        for item in soup.select(self.config.listing_selector)[:limit]:
            name_el = item.select_one(self.config.name_selector)
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            website_url = None
            has_website = None
            if self.config.website_selector:
                web_el = item.select_one(self.config.website_selector)
                if web_el:
                    website_url = web_el.get("href") or web_el.get_text(strip=True)
                    has_website = bool(website_url)
            listings.append(
                BusinessListing(
                    name=name,
                    source=self.config.source,
                    region=self.config.region,
                    has_website=has_website,
                    website_url=website_url,
                )
            )
        return listings

