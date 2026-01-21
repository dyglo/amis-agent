from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from amis_agent.core.config import get_settings


@dataclass(frozen=True)
class HttpResponse:
    url: str
    status_code: int
    text: str


class RateLimiter:
    def __init__(self):
        self._last_by_host: dict[str, float] = {}
        self._min_interval = 1.0 / max(get_settings().scrape_rate_limit_per_host, 1)

    def wait(self, host: str) -> None:
        now = time.time()
        last = self._last_by_host.get(host)
        if last is not None:
            delta = now - last
            if delta < self._min_interval:
                time.sleep(self._min_interval - delta)
        self._last_by_host[host] = time.time()


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
def fetch(url: str, *, timeout_s: int) -> HttpResponse:
    headers = {"User-Agent": get_settings().scrape_user_agent}
    with httpx.Client(timeout=timeout_s, headers=headers) as client:
        resp = client.get(url)
        return HttpResponse(url=url, status_code=resp.status_code, text=resp.text)


def ensure_allowed_domain(url: str) -> None:
    allowed = [d.strip() for d in get_settings().scrape_allowed_domains.split(",") if d.strip()]
    if not allowed:
        return
    host = urlparse(url).hostname or ""
    if not any(host == d or host.endswith(f".{d}") for d in allowed):
        raise ValueError("domain_not_allowed")

