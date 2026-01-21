from __future__ import annotations

from amis_agent.application.services.discovery import BusinessListing
from amis_agent.workers.discovery import map_listing_to_status


def test_map_listing_to_status_has_website():
    listing = BusinessListing(
        name="A",
        source="x",
        region="US",
        has_website=True,
        website_url="https://example.com",
    )
    status, url = map_listing_to_status(listing)
    assert status == "has_website"
    assert url == "https://example.com"


def test_map_listing_to_status_no_website():
    listing = BusinessListing(
        name="B",
        source="x",
        region="US",
        has_website=False,
        website_url=None,
    )
    status, url = map_listing_to_status(listing)
    assert status == "no_website"
    assert url is None

