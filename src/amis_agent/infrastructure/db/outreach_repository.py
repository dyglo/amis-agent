from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.application.services.outreach_processor import OutreachItem, OutreachResult
from amis_agent.infrastructure.db.models import LeadModel, OutreachModel


async def fetch_queued_outreach(session: AsyncSession, limit: int = 10) -> list[OutreachItem]:
    stmt = (
        select(OutreachModel, LeadModel)
        .join(LeadModel, OutreachModel.lead_id == LeadModel.id)
        .where(OutreachModel.status == "queued")
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    items = []
    for outreach, lead in rows:
        items.append(
            OutreachItem(
                outreach_id=outreach.id,
                to_email=lead.contact_email,
                subject=outreach.subject,
                body=outreach.body,
                region=lead.region,
                is_opt_in=bool(lead.opt_in),
            )
        )
    return items


async def apply_results(session: AsyncSession, results: Iterable[OutreachResult]) -> None:
    for result in results:
        stmt = select(OutreachModel).where(OutreachModel.id == result.outreach_id)
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            continue
        row.status = result.status
        row.sent_at = result.sent_at
    await session.commit()

