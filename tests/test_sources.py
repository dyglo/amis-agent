from __future__ import annotations

from amis_agent.infrastructure.connectors.sources import build_connectors


def test_build_connectors_returns_five():
    sources = build_connectors()
    assert len(sources) == 5
    names = {s.name for s in sources}
    assert {
        "i_need_a_plumber",
        "chamber_nyc",
        "localdirectory_contractors",
        "zipleaf_us",
        "zipleaf_uk",
    }.issubset(names)

