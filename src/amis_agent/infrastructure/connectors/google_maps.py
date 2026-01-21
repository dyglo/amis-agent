from __future__ import annotations

from amis_agent.application.services.discovery import BusinessListing


class GoogleMapsConnector:
    def fetch(self, *, region: str, limit: int) -> list[BusinessListing]:
        # TODO: implement API-based discovery
        return []

