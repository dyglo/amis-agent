from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import CompanyModel, LeadModel


async def fetch_leads_for_enrichment(session: AsyncSession, limit: int = 50) -> list[LeadModel]:
    stmt = (
        select(LeadModel)
        .where(LeadModel.status == "new")
        .where(LeadModel.contact_status == "pending")
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def fetch_existing_lead_keys(session: AsyncSession) -> set[tuple[str, str]]:
    stmt = select(CompanyModel.name, CompanyModel.website_domain).join(
        LeadModel, LeadModel.company_id == CompanyModel.id
    )
    rows = (await session.execute(stmt)).all()
    keys = set()
    for name, domain in rows:
        if name and domain:
            keys.add((" ".join(name.strip().lower().split()), domain.lower()))
    return keys


async def create_lead(
    session: AsyncSession,
    *,
    company_id: int,
    region: str | None,
    contact_email: str | None,
    contact_status: str,
    status: str,
    contact_id: int | None = None,
) -> LeadModel:
    lead = LeadModel(
        company_id=company_id,
        region=region,
        contact_email=contact_email,
        contact_status=contact_status,
        status=status,
        contact_id=contact_id,
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead


async def update_lead(
    session: AsyncSession,
    lead: LeadModel,
    *,
    contact_email: str | None = None,
    contact_status: str | None = None,
    status: str | None = None,
    contact_id: int | None = None,
) -> LeadModel:
    if contact_email is not None:
        lead.contact_email = contact_email
    if contact_status is not None:
        lead.contact_status = contact_status
    if status is not None:
        lead.status = status
    if contact_id is not None:
        lead.contact_id = contact_id
    await session.commit()
    await session.refresh(lead)
    return lead
