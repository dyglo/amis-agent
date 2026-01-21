from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.company_repository import upsert_company
from amis_agent.infrastructure.db.lead_repository import create_lead
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel
from amis_agent.infrastructure.db.outbox_repository import create_llm_draft, fetch_existing_draft
from amis_agent.infrastructure.db.qualification_repository import upsert_qualification


@dataclass(frozen=True)
class DemoSeed:
    name: str
    website_url: str
    region: str
    source: str


DEMO_SEEDS: list[DemoSeed] = [
    DemoSeed(name="Adobe", website_url="https://www.adobe.com", region="US", source="demo_seed"),
    DemoSeed(name="Atlassian", website_url="https://www.atlassian.com", region="US", source="demo_seed"),
    DemoSeed(name="Cisco", website_url="https://www.cisco.com", region="US", source="demo_seed"),
    DemoSeed(name="HubSpot", website_url="https://www.hubspot.com", region="US", source="demo_seed"),
    DemoSeed(name="IBM", website_url="https://www.ibm.com", region="US", source="demo_seed"),
    DemoSeed(name="Intuit", website_url="https://www.intuit.com", region="US", source="demo_seed"),
    DemoSeed(name="Oracle", website_url="https://www.oracle.com", region="US", source="demo_seed"),
    DemoSeed(name="Salesforce", website_url="https://www.salesforce.com", region="US", source="demo_seed"),
    DemoSeed(name="Shopify", website_url="https://www.shopify.com", region="US", source="demo_seed"),
    DemoSeed(name="Twilio", website_url="https://www.twilio.com", region="US", source="demo_seed"),
]


async def seed_demo_data(session: AsyncSession, *, force: bool = False) -> dict:
    company_count = await session.scalar(select(CompanyModel.id).limit(1))
    if company_count and not force:
        return {"seeded": False, "reason": "not_empty"}

    seeded_companies = 0
    seeded_leads = 0
    seeded_outbox = 0
    for seed in DEMO_SEEDS:
        existing_company = (
            await session.execute(
                select(CompanyModel)
                .where(CompanyModel.name == seed.name)
                .where(CompanyModel.region == seed.region)
                .where(CompanyModel.source == seed.source)
            )
        ).scalar_one_or_none()
        company = existing_company or await upsert_company(
            session,
            name=seed.name,
            region=seed.region,
            website_status="has_website",
            website_url=seed.website_url,
            source=seed.source,
        )
        if existing_company is None:
            seeded_companies += 1
        await upsert_qualification(
            session,
            company_id=company.id,
            decision="qualified",
            score=100,
            reason="demo_seed",
        )

        existing_lead = (
            await session.execute(select(LeadModel).where(LeadModel.company_id == company.id))
        ).scalar_one_or_none()
        if existing_lead:
            lead = existing_lead
            if lead.status != "ready_for_review":
                lead.status = "ready_for_review"
                await session.commit()
        else:
            lead = await create_lead(
                session,
                company_id=company.id,
                region=seed.region,
                contact_email=None,
                contact_status="missing_email",
                status="ready_for_review",
            )
            seeded_leads += 1

        existing = await fetch_existing_draft(session, lead_id=lead.id)
        if existing:
            continue

        subject_variants = [
            "Introducing Amis Agent",
            "Amis Agent: automation for your team",
            "Quick intro: Amis Agent",
        ]
        body_text = (
            "Hi,\n\n"
            "I’m reaching out to introduce Amis Agent, a solution that streamlines workflows "
            "and automates repetitive tasks. We help teams move faster with reliable, "
            "production-ready automation.\n\n"
            "If helpful, I can share a brief 10-minute demo this week.\n\n"
            "Best regards,\n"
            "Tafar M"
        )
        await create_llm_draft(
            session,
            lead_id=lead.id,
            to_email=None,
            subject=subject_variants[0],
            subject_variants=subject_variants,
            body_text=body_text,
            body_html=None,
            followup_text="Following up in case this is relevant.",
            personalization_vars={"company_name": company.name},
            personalization_fact=None,
            personalization_source_url=None,
            prompt_hash=f"demo-{company.id}",
            llm_model="demo",
            llm_latency_ms=None,
            llm_token_usage=None,
            llm_confidence=0.1,
            llm_rationale="demo_seed",
            status="ready_for_review",
        )
        seeded_outbox += 1

    return {
        "seeded": True,
        "companies": seeded_companies,
        "leads": seeded_leads,
        "outbox": seeded_outbox,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
