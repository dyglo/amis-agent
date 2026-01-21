from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from amis_agent.application.services.discovery import BusinessListing
from amis_agent.core.config import get_settings
from amis_agent.core.logging import get_logger


logger = get_logger(worker="discovery_seed")


@dataclass(frozen=True)
class SeedCompany:
    name: str
    website_url: str
    region: str
    source: str


DEFAULT_SEEDS: list[SeedCompany] = [
    SeedCompany(name="Adobe", website_url="https://www.adobe.com", region="US", source="seed_static"),
    SeedCompany(name="Atlassian", website_url="https://www.atlassian.com", region="US", source="seed_static"),
    SeedCompany(name="Cisco", website_url="https://www.cisco.com", region="US", source="seed_static"),
    SeedCompany(name="HubSpot", website_url="https://www.hubspot.com", region="US", source="seed_static"),
    SeedCompany(name="IBM", website_url="https://www.ibm.com", region="US", source="seed_static"),
    SeedCompany(name="Intuit", website_url="https://www.intuit.com", region="US", source="seed_static"),
    SeedCompany(name="Oracle", website_url="https://www.oracle.com", region="US", source="seed_static"),
    SeedCompany(name="Salesforce", website_url="https://www.salesforce.com", region="US", source="seed_static"),
    SeedCompany(name="Shopify", website_url="https://www.shopify.com", region="US", source="seed_static"),
    SeedCompany(name="Twilio", website_url="https://www.twilio.com", region="US", source="seed_static"),
]


def _load_seed_file(path: str) -> list[SeedCompany]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.warning("discovery_seed_invalid_json", path=path)
        return []
    if not isinstance(raw, list):
        return []
    seeds: list[SeedCompany] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        website_url = str(item.get("website_url") or "").strip()
        region = str(item.get("region") or "US").strip() or "US"
        source = str(item.get("source") or "seed_static").strip() or "seed_static"
        if not name or not website_url:
            continue
        seeds.append(
            SeedCompany(
                name=name,
                website_url=website_url,
                region=region,
                source=source,
            )
        )
    return seeds


class StaticSeedConnector:
    def __init__(self, seeds: list[SeedCompany] | None = None):
        self.seeds = seeds or []

    def fetch(self, *, region: str, limit: int) -> list[BusinessListing]:
        if not self.seeds:
            return []
        rows = [s for s in self.seeds if s.region == region][:limit]
        return [
            BusinessListing(
                name=s.name,
                source=s.source,
                region=s.region,
                has_website=True,
                website_url=s.website_url,
            )
            for s in rows
        ]


def build_seed_connector() -> StaticSeedConnector:
    settings = get_settings()
    if not settings.discovery_seed_enabled:
        return StaticSeedConnector([])
    seeds = _load_seed_file(settings.discovery_seed_path)
    if not seeds:
        seeds = DEFAULT_SEEDS
    return StaticSeedConnector(seeds)
