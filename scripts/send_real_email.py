from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from sqlalchemy import select

from amis_agent.application.services.email import EmailMessage
from amis_agent.application.services.email_render import render_email_body
from amis_agent.application.services.preflight import run_preflight
from amis_agent.core.config import get_settings
from amis_agent.core.signature import load_signature
from amis_agent.infrastructure.db.audit_repository import log_audit
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel
from amis_agent.infrastructure.db.session import SessionLocal
from amis_agent.infrastructure.email.gmail_sender import from_settings


load_dotenv()


@dataclass(frozen=True)
class SendResult:
    status: str
    response: dict | None


def send_real_email(to_email: str, subject: str, body: str) -> SendResult:
    sender = from_settings()
    settings = get_settings()
    signature = load_signature()
    message = EmailMessage(
        to_email=to_email,
        subject=subject,
        body=render_email_body(body_text=body, signature=signature),
        from_email=settings.email_from,
        from_name=settings.email_display_name,
    )
    response = sender.send(message)
    return SendResult(status="sent", response=response)

async def send_outbox_email(outbox_id: int) -> SendResult:
    settings = get_settings()
    signature = load_signature()
    sender = from_settings()
    async with SessionLocal() as session:
        draft = (
            await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
        ).scalar_one_or_none()
        if not draft:
            raise SystemExit(f"outbox_id_not_found:{outbox_id}")
        lead = (
            await session.execute(select(LeadModel).where(LeadModel.id == draft.lead_id))
        ).scalar_one_or_none()
        company = None
        if lead:
            company = (
                await session.execute(select(CompanyModel).where(CompanyModel.id == lead.company_id))
            ).scalar_one_or_none()
        if not lead or not company:
            raise SystemExit("lead_or_company_missing")
        preflight = run_preflight(outbox=draft, lead=lead, company=company, signature=signature)
        preflight.details["sender_email"] = settings.gmail_sender
        await log_audit(
            session,
            action="send_preflight",
            source="send_real_email",
            details=preflight.details,
        )
        if not preflight.allowed:
            raise SystemExit("preflight_failed")
        message = EmailMessage(
            to_email=draft.to_email,
            subject=draft.subject,
            body=render_email_body(body_text=draft.body_text, signature=signature),
            from_email=settings.email_from,
            from_name=settings.email_display_name,
        )
        response = sender.send(message)
        draft.status = "sent"
        await session.commit()
        return SendResult(status="sent", response=response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox-id", type=int, default=None)
    args = parser.parse_args()
    if args.outbox_id is not None:
        import asyncio

        result = asyncio.run(send_outbox_email(args.outbox_id))
        print(result)
        return
    to_email = os.environ.get("REAL_EMAIL_TO")
    if not to_email:
        raise SystemExit("REAL_EMAIL_TO is required to run this script")
    subject = os.environ.get("REAL_EMAIL_SUBJECT", "AMIS Agent Test")
    body = os.environ.get("REAL_EMAIL_BODY", "This is a real send test.")
    result = send_real_email(to_email, subject, body)
    print(result)


if __name__ == "__main__":
    main()

