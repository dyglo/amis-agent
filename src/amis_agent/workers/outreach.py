from __future__ import annotations

import asyncio

from amis_agent.application.services.outreach_processor import process_outreach_items
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.db.outreach_repository import apply_results, fetch_queued_outreach
from amis_agent.infrastructure.db.session import SessionLocal
from amis_agent.infrastructure.db.suppression_repository import fetch_suppressed_emails
from amis_agent.infrastructure.email.gmail_sender import from_settings
from amis_agent.infrastructure.queue.rate_limit import RateLimiter


logger = get_logger(worker="outreach")


class InMemorySuppressionStore:
    def __init__(self, suppressed: set[str]):
        self._suppressed = suppressed

    def is_suppressed(self, email: str) -> bool:
        return email in self._suppressed


def run() -> None:
    asyncio.run(run_async())


async def run_async() -> None:
    sender = from_settings()
    limiter = RateLimiter()
    async with SessionLocal() as session:
        items = await fetch_queued_outreach(session)
        emails = [i.to_email for i in items if i.to_email]
        suppressed = await fetch_suppressed_emails(session, emails)
        store = InMemorySuppressionStore(suppressed)
        results = process_outreach_items(
            items,
            sender=sender,
            suppression_store=store,
            limit_store=limiter,
        )
        await apply_results(session, results)
    logger.info("outreach_job_finished", processed=len(items))

