from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from amis_agent.core.logging import get_logger


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
    logger = get_logger(worker="discovery_service")
    listings: list[BusinessListing] = []
    for connector in connectors:
        try:
            results = connector.fetch(region=region, limit=limit)
        except Exception as exc:  # pragma: no cover - defensive safety
            logger.warning("discovery_connector_failed", error=str(exc))
            continue
        listings.extend(results)
    return listings

