from __future__ import annotations

from dataclasses import dataclass

from amis_agent.core.config import get_settings
from amis_agent.infrastructure.connectors.directory_scraper import DirectoryScrapeConfig, GenericDirectoryConnector


@dataclass(frozen=True)
class DummyResponse:
    url: str
    status_code: int
    text: str


def test_directory_scraper_parses_listings(monkeypatch):
    html = """
    <div class='listing'>
      <span class='name'>Alpha Co</span>
      <a class='website' href='https://alpha.example.com'>Website</a>
    </div>
    <div class='listing'>
      <span class='name'>Beta LLC</span>
    </div>
    """

    def fetcher(url: str, timeout: int):
        return DummyResponse(url=url, status_code=200, text=html)

    # allow domain
    monkeypatch.setenv("SCRAPE_ALLOWED_DOMAINS", "example.com")
    get_settings.cache_clear()

    cfg = DirectoryScrapeConfig(
        base_url="https://example.com/directory",
        listing_selector=".listing",
        name_selector=".name",
        website_selector=".website",
        region="US",
        source="example_dir",
    )
    connector = GenericDirectoryConnector(cfg, fetcher=fetcher, check_robots=False)
    results = connector.fetch(region="US", limit=10)

    assert len(results) == 2
    assert results[0].name == "Alpha Co"
    assert results[0].has_website is True
    assert results[1].name == "Beta LLC"
    assert results[1].has_website is None

