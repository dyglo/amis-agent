from __future__ import annotations

from amis_agent.infrastructure.db.base import Base
from amis_agent.infrastructure.db import models  # noqa: F401


def test_models_registered():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "companies",
        "leads",
        "outreach",
        "replies",
        "suppression",
        "audit_log",
        "company_qualification",
        "contacts",
        "outbox",
        "industry_insights",
        "reply_patterns",
    }
    assert expected.issubset(table_names)

