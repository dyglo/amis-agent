from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from amis_agent.application.services.email import EmailMessage
from amis_agent.application.services.email_render import render_email_body
from amis_agent.application.services.preflight import run_preflight
from amis_agent.core.config import get_settings
from amis_agent.core.logging import get_logger
from amis_agent.core.signature import load_signature
from amis_agent.infrastructure.db.audit_repository import log_audit
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel
from amis_agent.infrastructure.db.outbox_repository import fetch_approved, mark_sent
from amis_agent.infrastructure.db.session import SessionLocal
from amis_agent.infrastructure.email.gmail_sender import from_settings
from amis_agent.infrastructure.queue.rate_limit import RateLimiter
from amis_agent.infrastructure.queue.send_health import SendHealthMonitor


logger = get_logger(worker="outbox_sender")


def run() -> None:
    asyncio.run(run_async())


async def run_async() -> None:
    sender = from_settings()
    limiter = RateLimiter()
    health = SendHealthMonitor()
    settings = get_settings()
    signature = load_signature()
    async with SessionLocal() as session:
        drafts = await fetch_approved(session)
        if health.is_paused():
            logger.warning("send_paused_error_spike", count=len(drafts))
            return
        for draft in drafts:
            if not draft.to_email:
                continue
            lead = (
                await session.execute(select(LeadModel).where(LeadModel.id == draft.lead_id))
            ).scalar_one_or_none()
            company = None
            if lead:
                company = (
                    await session.execute(
                        select(CompanyModel).where(CompanyModel.id == lead.company_id)
                    )
                ).scalar_one_or_none()
            if not lead or not company:
                continue
            domain = draft.to_email.split("@", 1)[-1].lower() if "@" in draft.to_email else None
            now = datetime.now(timezone.utc)
            if not limiter.can_send(now, domain):
                continue
            preflight = run_preflight(outbox=draft, lead=lead, company=company, signature=signature)
            preflight.details["sender_email"] = settings.gmail_sender
            await log_audit(
                session,
                action="send_preflight",
                source="outbox_sender",
                details=preflight.details,
            )
            if not preflight.allowed:
                logger.warning("send_preflight_failed", outbox_id=draft.id)
                continue
            try:
                body = render_email_body(body_text=draft.body_text, signature=signature)
                message = EmailMessage(
                    to_email=draft.to_email,
                    subject=draft.subject,
                    body=body,
                    from_email=settings.email_from,
                    from_name=settings.email_display_name,
                )
                sender.send(message)
            except Exception:  # noqa: BLE001
                health.record_error()
                continue
            limiter.record_send(now, domain)
            await mark_sent(session, draft)
            lead.status = "sent"
            await session.commit()
        logger.info("outbox_sender_finished", sent=len(drafts))
