from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import SuppressionModel


async def fetch_suppressed_emails(
    session: AsyncSession, emails: Iterable[str]
) -> set[str]:
    email_list = list({e for e in emails if e})
    if not email_list:
        return set()
    stmt = select(SuppressionModel.email).where(SuppressionModel.email.in_(email_list))
    rows = (await session.execute(stmt)).all()
    return {row[0] for row in rows}

