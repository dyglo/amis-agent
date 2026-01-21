from __future__ import annotations

from dataclasses import dataclass

from amis_agent.infrastructure.connectors.directory_scraper import DirectoryScrapeConfig, GenericDirectoryConnector


@dataclass(frozen=True)
class SourceConfig:
    name: str
    connector: GenericDirectoryConnector


def build_connectors() -> list[SourceConfig]:
    sources: list[SourceConfig] = []

    sources.append(
        SourceConfig(
            name="i_need_a_plumber",
            connector=GenericDirectoryConnector(
                DirectoryScrapeConfig(
                    base_url="https://i-need-a-plumber.us/",
                    listing_selector="table tbody tr",
                    name_selector="td:nth-child(1)",
                    website_selector="td:nth-child(2)",
                    region="US",
                    source="i_need_a_plumber",
                ),
                check_robots=False,
            ),
        )
    )

    sources.append(
        SourceConfig(
            name="chamber_nyc",
            connector=GenericDirectoryConnector(
                DirectoryScrapeConfig(
                    base_url="https://chamber.nyc/business-directory?businessNameLetter=I",
                    listing_selector="div.post-style1",
                    name_selector="h3",
                    website_selector="a[href^='http']",
                    region="US",
                    source="chamber_nyc",
                )
            ),
        )
    )

    sources.append(
        SourceConfig(
            name="localdirectory_contractors",
            connector=GenericDirectoryConnector(
                DirectoryScrapeConfig(
                    base_url="https://localdirectory.contractors/contractors/",
                    listing_selector="div.card.h-100",
                    name_selector=".geodir-entry-title a",
                    website_selector=None,
                    region="US",
                    source="localdirectory_contractors",
                )
            ),
        )
    )

    sources.append(
        SourceConfig(
            name="zipleaf_us",
            connector=GenericDirectoryConnector(
                DirectoryScrapeConfig(
                    base_url="https://www.zipleaf.us/Updated-Companies",
                    listing_selector=".results2 ul.listivews > li",
                    name_selector="a.g_link",
                    website_selector=None,
                    region="US",
                    source="zipleaf_us",
                )
            ),
        )
    )

    sources.append(
        SourceConfig(
            name="zipleaf_uk",
            connector=GenericDirectoryConnector(
                DirectoryScrapeConfig(
                    base_url="https://www.zipleaf.co.uk/Updated-Companies",
                    listing_selector=".results2 ul.listivews > li",
                    name_selector="a.g_link",
                    website_selector=None,
                    region="UK",
                    source="zipleaf_uk",
                )
            ),
        )
    )

    return sources

