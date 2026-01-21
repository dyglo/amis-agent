from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "N/A")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")
os.environ.setdefault("GOOGLE_CREDENTIALS_FILE", "/tmp/creds.json")
os.environ.setdefault("GOOGLE_TOKEN_FILE", "/tmp/token.json")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from amis_agent.api.deps import get_db_session
from amis_agent.core.config import get_settings
from amis_agent.infrastructure.db.base import Base
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel
from amis_agent.main import create_app


async def _init_db() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _app_with_session(session_factory: async_sessionmaker[AsyncSession]) -> TestClient:
    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    return TestClient(app)


def test_admin_auth_guard_blocks_without_token():
    get_settings.cache_clear()
    session_factory = asyncio.run(_init_db())
    client = _app_with_session(session_factory)
    res = client.get("/api/outbox")
    assert res.status_code == 401


def test_approve_outbox_updates_status():
    get_settings.cache_clear()
    session_factory = asyncio.run(_init_db())
    client = _app_with_session(session_factory)

    async def seed():
        async with session_factory() as session:
            company = CompanyModel(name="Acme", website_url="https://acme.test")
            session.add(company)
            await session.flush()
            lead = LeadModel(company_id=company.id, contact_email="a@acme.test", status="ready_for_review")
            session.add(lead)
            await session.flush()
            outbox = OutboxModel(
                lead_id=lead.id,
                to_email="a@acme.test",
                subject="Hello",
                body_text="Hello Acme.",
                status="ready_for_review",
                personalization_fact="I noticed your website at https://acme.test.",
                personalization_source_url="https://acme.test",
            )
            session.add(outbox)
            await session.commit()
            return outbox.id

    outbox_id = asyncio.run(seed())
    res = client.post(
        f"/api/outbox/{outbox_id}/approve",
        headers={"X-ADMIN-TOKEN": "test-token"},
    )
    assert res.status_code == 200

    async def fetch():
        async with session_factory() as session:
            return (
                await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
            ).scalar_one()

    outbox = asyncio.run(fetch())
    assert outbox.status == "approved"
    assert outbox.approved_by_human is True


def test_send_blocked_when_enable_sending_false():
    os.environ["ENABLE_SENDING"] = "false"
    get_settings.cache_clear()
    session_factory = asyncio.run(_init_db())
    client = _app_with_session(session_factory)

    async def seed():
        async with session_factory() as session:
            company = CompanyModel(name="Acme", website_url="https://acme.test")
            session.add(company)
            await session.flush()
            lead = LeadModel(
                company_id=company.id,
                contact_email="a@acme.test",
                status="ready_for_review",
                contact_status="found",
            )
            session.add(lead)
            await session.flush()
            outbox = OutboxModel(
                lead_id=lead.id,
                to_email="a@acme.test",
                subject="Hello",
                body_text="Hello Acme.",
                status="approved",
                approved_by_human=True,
                personalization_fact="I noticed your website at https://acme.test.",
                personalization_source_url="https://acme.test",
            )
            session.add(outbox)
            await session.commit()
            return outbox.id

    outbox_id = asyncio.run(seed())
    res = client.post(
        f"/api/outbox/{outbox_id}/send",
        headers={"X-ADMIN-TOKEN": "test-token"},
    )
    assert res.status_code == 400
    assert "sending_disabled" in res.json()["detail"]
