from __future__ import annotations

from dataclasses import dataclass

from amis_agent.application.services.discovery import BusinessListing, discover_businesses
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.connectors.sources import build_connectors
from amis_agent.infrastructure.db.company_repository import upsert_company
from amis_agent.infrastructure.db.session import SessionLocal


logger = get_logger(worker="discovery")


@dataclass(frozen=True)
class DiscoveryResult:
    total: int
    inserted: int


def map_listing_to_status(listing: BusinessListing) -> tuple[str | None, str | None]:
    if listing.has_website is True:
        return "has_website", listing.website_url
    if listing.has_website is False:
        return "no_website", None
    return None, listing.website_url


def run() -> None:
    connectors = build_connectors()
    listings = discover_businesses(
        [c.connector for c in connectors], region="US", limit=50
    )

    inserted = 0
    if listings:
        async def _persist() -> int:
            count = 0
            async with SessionLocal() as session:
                for listing in listings:
                    status, website_url = map_listing_to_status(listing)
                    await upsert_company(
                        session,
                        name=listing.name,
                        region=listing.region,
                        website_status=status,
                        website_url=website_url,
                        source=listing.source,
                    )
                    count += 1
            return count

        import asyncio

        inserted = asyncio.run(_persist())

    logger.info("discovery_job_finished", total=len(listings), inserted=inserted)

