from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import CompanyModel


async def upsert_company(
    session: AsyncSession,
    *,
    name: str,
    region: str | None,
    website_status: str | None,
    website_url: str | None,
    source: str | None,
) -> CompanyModel:
    stmt = (
        select(CompanyModel)
        .where(CompanyModel.name == name)
        .where(CompanyModel.region == region)
        .where(CompanyModel.source == source)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.website_status = website_status or existing.website_status
        existing.website_url = website_url or existing.website_url
        await session.commit()
        return existing

    company = CompanyModel(
        name=name,
        region=region,
        website_status=website_status,
        website_url=website_url,
        source=source,
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company

