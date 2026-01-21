from __future__ import annotations

from amis_agent.application.services.discovery import BusinessListing, discover_businesses


class DummyConnector:
    def __init__(self, name: str):
        self.name = name

    def fetch(self, *, region: str, limit: int):
        return [
            BusinessListing(
                name=f"Biz-{self.name}",
                source=self.name,
                region=region,
                has_website=False,
                website_url=None,
            )
        ]


def test_discover_businesses_aggregates():
    connectors = [DummyConnector("a"), DummyConnector("b")]
    results = discover_businesses(connectors, region="US", limit=10)
    assert len(results) == 2
    assert {r.source for r in results} == {"a", "b"}

