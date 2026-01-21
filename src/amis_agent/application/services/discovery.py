from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BusinessListing:
    name: str
    source: str
    region: str | None
    has_website: bool | None
    website_url: str | None


class DiscoveryConnector(Protocol):
    def fetch(self, *, region: str, limit: int) -> list[BusinessListing]:  # pragma: no cover
        ...


def discover_businesses(connectors: list[DiscoveryConnector], *, region: str, limit: int) -> list[BusinessListing]:
    listings: list[BusinessListing] = []
    for connector in connectors:
        results = connector.fetch(region=region, limit=limit)
        listings.extend(results)
    return listings

