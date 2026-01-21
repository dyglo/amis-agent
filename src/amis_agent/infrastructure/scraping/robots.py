from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from amis_agent.infrastructure.scraping.http_client import fetch


@dataclass
class RobotsCache:
    cache: dict[str, RobotFileParser]

    def get(self, base_url: str, user_agent: str) -> RobotFileParser:
        host = urlparse(base_url).netloc
        if host in self.cache:
            return self.cache[host]
        robots_url = urljoin(base_url, "/robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            resp = fetch(robots_url, timeout_s=10)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                parser.disallow_all = False
        except Exception:  # noqa: BLE001
            parser.disallow_all = False
        self.cache[host] = parser
        return parser

