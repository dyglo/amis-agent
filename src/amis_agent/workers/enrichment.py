from __future__ import annotations

import asyncio

from sqlalchemy import select

from amis_agent.application.services.llm_email_writer import write_outbox_draft
from amis_agent.application.services.templates import pick_persona
from amis_agent.application.services.enrichment import EmailEnricher
from amis_agent.application.services.lead_pipeline import assert_transition
from amis_agent.core.config import get_settings
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.db.contact_repository import upsert_contact
from amis_agent.infrastructure.db.lead_repository import create_lead, fetch_leads_for_enrichment, update_lead
from amis_agent.infrastructure.db.models import CompanyModel, ContactModel, LeadModel
from amis_agent.infrastructure.db.memory_repository import get_industry_insight
from amis_agent.infrastructure.db.session import SessionLocal
from urllib.parse import urlparse


logger = get_logger(worker="enrichment")


def run() -> None:
    asyncio.run(run_async())


async def run_async() -> None:
    settings = get_settings()
    enricher = EmailEnricher()
    async with SessionLocal() as session:
        leads = await fetch_leads_for_enrichment(session)
        processed = 0
        for lead in leads:
            company = (
                await session.execute(select(CompanyModel).where(CompanyModel.id == lead.company_id))
            ).scalar_one_or_none()
            if not company or not company.website_url:
                await update_lead(session, lead, contact_status="missing_email", status="enriched")
                processed += 1
                continue
            allowed_domains = {
                d.strip().lower()
                for d in settings.enrich_allowed_domains.split(",")
                if d.strip()
            }
            if allowed_domains:
                host = urlparse(company.website_url).hostname or ""
                if not any(host == d or host.endswith(f".{d}") for d in allowed_domains):
                    await update_lead(session, lead, contact_status="missing_email", status="enriched")
                    processed += 1
                    continue

            result = enricher.enrich(
                website_url=company.website_url,
                user_agent=settings.scrape_user_agent,
                timeout_s=settings.scrape_timeout_s,
            )
            if result.personalization_line and company.about_snippet != result.personalization_line:
                company.about_snippet = result.personalization_line
                await session.commit()

            if not result.emails:
                await update_lead(session, lead, contact_status="missing_email", status="enriched")
                processed += 1
                continue

            primary = result.emails[0]
            contact = await upsert_contact(
                session,
                company_id=company.id,
                email=primary.email,
                source_url=primary.source_url,
                confidence=primary.confidence,
            )
            await update_lead(
                session,
                lead,
                contact_email=primary.email,
                contact_status="found",
                status="enriched",
                contact_id=contact.id,
            )

            for extra in result.emails[1:]:
                contact_extra = await upsert_contact(
                    session,
                    company_id=company.id,
                    email=extra.email,
                    source_url=extra.source_url,
                    confidence=extra.confidence,
                )
                await create_lead(
                    session,
                    company_id=company.id,
                    region=company.region,
                    contact_email=extra.email,
                    contact_status="found",
                    status="enriched",
                    contact_id=contact_extra.id,
                )

            processed += 1

        await _generate_drafts(session)
        logger.info("enrichment_job_finished", processed=processed, drafts="generated")


async def _generate_drafts(session) -> None:
    stmt = (
        select(LeadModel, CompanyModel, ContactModel)
        .join(CompanyModel, LeadModel.company_id == CompanyModel.id)
        .outerjoin(ContactModel, LeadModel.contact_id == ContactModel.id)
        .where(LeadModel.status == "enriched")
        .where(LeadModel.contact_status.in_(["found", "missing_email"]))
    )
    rows = (await session.execute(stmt)).all()
    for lead, company, contact in rows:
        insight = await get_industry_insight(session, company.industry)
        persona = insight.preferred_persona if insight and insight.preferred_persona else pick_persona(
            company.industry
        )
        snippets = {
            "about": company.about_snippet,
            "contact": None,
        }
        value_props = [
            "automation of repetitive tasks",
            "faster response times",
            "reduced operational overhead",
        ]
        tone_by_persona = {
            "Founder": "formal, concise, founder-to-founder",
            "CTO": "formal, technical, concise",
            "Ops": "formal, operations-focused, concise",
        }
        await write_outbox_draft(
            session,
            lead=lead,
            company=company,
            contact=contact,
            snippets=snippets,
            value_props=value_props,
            persona=persona,
            tone=tone_by_persona.get(persona, "formal, concise"),
            status="ready_for_review",
        )
        assert_transition(lead.status, "ready_for_review")
        await update_lead(session, lead, status="ready_for_review")
