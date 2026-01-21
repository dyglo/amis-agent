from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import IndustryInsightModel, ReplyPatternModel


async def get_industry_insight(
    session: AsyncSession, industry: str | None
) -> IndustryInsightModel | None:
    if not industry:
        return None
    stmt = select(IndustryInsightModel).where(IndustryInsightModel.industry == industry)
    return (await session.execute(stmt)).scalar_one_or_none()


async def upsert_reply_pattern(
    session: AsyncSession,
    *,
    pattern_text: str,
    classification: str | None = None,
) -> ReplyPatternModel:
    stmt = select(ReplyPatternModel).where(ReplyPatternModel.pattern_text == pattern_text)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.occurrences += 1
        if classification:
            existing.classification = classification
        await session.commit()
        return existing

    pattern = ReplyPatternModel(
        pattern_text=pattern_text,
        classification=classification,
        occurrences=1,
    )
    session.add(pattern)
    await session.commit()
    await session.refresh(pattern)
    return pattern
