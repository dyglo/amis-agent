from __future__ import annotations

from amis_agent.application.services.discovery import BusinessListing


class RegistryConnector:
    def fetch(self, *, region: str, limit: int) -> list[BusinessListing]:
        # TODO: implement registry discovery
        return []

