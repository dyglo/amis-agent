from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import CompanyModel, CompanyQualificationModel


async def fetch_unqualified_companies(session: AsyncSession, limit: int = 100) -> list[CompanyModel]:
    stmt = (
        select(CompanyModel)
        .outerjoin(CompanyQualificationModel, CompanyQualificationModel.company_id == CompanyModel.id)
        .where(CompanyQualificationModel.id.is_(None))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def upsert_qualification(
    session: AsyncSession,
    *,
    company_id: int,
    decision: str,
    score: int,
    reason: str | None,
) -> CompanyQualificationModel:
    stmt = select(CompanyQualificationModel).where(CompanyQualificationModel.company_id == company_id)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.decision = decision
        existing.score = score
        existing.reason = reason
        await session.commit()
        return existing

    entry = CompanyQualificationModel(
        company_id=company_id,
        decision=decision,
        score=score,
        reason=reason,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
