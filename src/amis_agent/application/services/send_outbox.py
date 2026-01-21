from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.application.services.email import EmailMessage
from amis_agent.application.services.email_render import render_email_body
from amis_agent.application.services.preflight import run_preflight
from amis_agent.core.config import get_settings
from amis_agent.core.signature import load_signature
from amis_agent.infrastructure.db.audit_repository import log_audit
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel
from amis_agent.infrastructure.email.gmail_sender import from_settings


@dataclass(frozen=True)
class SendResult:
    status: str
    response: dict | None


class SendBlockedError(RuntimeError):
    pass


async def send_outbox_draft(session: AsyncSession, outbox_id: int) -> SendResult:
    settings = get_settings()
    if not settings.enable_sending:
        raise SendBlockedError("sending_disabled")

    signature = load_signature()
    sender = from_settings()
    draft = (
        await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
    ).scalar_one_or_none()
    if not draft:
        raise SendBlockedError(f"outbox_id_not_found:{outbox_id}")

    lead = (
        await session.execute(select(LeadModel).where(LeadModel.id == draft.lead_id))
    ).scalar_one_or_none()
    company = None
    if lead:
        company = (
            await session.execute(select(CompanyModel).where(CompanyModel.id == lead.company_id))
        ).scalar_one_or_none()
    if not lead or not company:
        raise SendBlockedError("lead_or_company_missing")

    preflight = run_preflight(outbox=draft, lead=lead, company=company, signature=signature)
    preflight.details["sender_email"] = settings.gmail_sender
    preflight.details["enable_sending"] = settings.enable_sending
    await log_audit(
        session,
        action="send_preflight",
        source="api_send",
        details=preflight.details,
    )
    if not preflight.allowed:
        raise SendBlockedError("preflight_failed")

    message = EmailMessage(
        to_email=draft.to_email,
        subject=draft.subject,
        body=render_email_body(body_text=draft.body_text, signature=signature),
        from_email=settings.email_from,
        from_name=settings.email_display_name,
    )
    response = sender.send(message)
    draft.status = "sent"
    lead.status = "sent"
    await session.commit()
    return SendResult(status="sent", response=response)
