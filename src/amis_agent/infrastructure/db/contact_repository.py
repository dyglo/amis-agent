from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import ContactModel


async def upsert_contact(
    session: AsyncSession,
    *,
    company_id: int,
    email: str,
    source_url: str | None,
    confidence: int,
) -> ContactModel:
    stmt = select(ContactModel).where(ContactModel.company_id == company_id).where(
        ContactModel.email == email
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        if source_url:
            existing.source_url = source_url
        if confidence > existing.confidence:
            existing.confidence = confidence
        await session.commit()
        return existing

    contact = ContactModel(
        company_id=company_id,
        email=email,
        source_url=source_url,
        confidence=confidence,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def fetch_contacts_for_company(session: AsyncSession, company_id: int) -> list[ContactModel]:
    stmt = select(ContactModel).where(ContactModel.company_id == company_id)
    return list((await session.execute(stmt)).scalars().all())
