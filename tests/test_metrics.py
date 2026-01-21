from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")

from fastapi.testclient import TestClient

from amis_agent.main import create_app


def test_metrics_endpoint_exposes_metrics():
    app = create_app()
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200

    res = client.get("/metrics")
    assert res.status_code == 200
    assert "amis_http_requests_total" in res.text

