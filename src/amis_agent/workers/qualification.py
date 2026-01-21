from __future__ import annotations

from amis_agent.application.services.qualification import (
    extract_domain,
    qualify_company,
    should_dedupe,
)
from amis_agent.core.config import get_settings
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.db.lead_repository import create_lead, fetch_existing_lead_keys
from amis_agent.infrastructure.db.qualification_repository import (
    fetch_unqualified_companies,
    upsert_qualification,
)
from amis_agent.infrastructure.db.session import SessionLocal


logger = get_logger(worker="qualification")


def run() -> None:
    logger.info("qualification_job_started")
    settings = get_settings()
    allowed_sources = {s.strip() for s in settings.qualify_allowed_sources.split(",") if s.strip()}
    allowed_sources.update({"seed_static", "demo_seed"})
    allowed_domains = {
        d.strip().lower()
        for d in settings.qualify_allowed_domains.split(",")
        if d.strip()
    }

    async def _run() -> dict:
        async with SessionLocal() as session:
            companies = await fetch_unqualified_companies(session)
            existing_keys = await fetch_existing_lead_keys(session)
            qualified = 0
            created = 0
            for company in companies:
                domain = extract_domain(company.website_url)
                if domain and company.website_domain != domain:
                    company.website_domain = domain
                    await session.commit()

                decision = qualify_company(
                    name=company.name,
                    website_status=company.website_status,
                    website_url=company.website_url,
                    region=company.region,
                    source=company.source,
                    allowed_sources=allowed_sources,
                    allowed_domains=allowed_domains,
                )
                await upsert_qualification(
                    session,
                    company_id=company.id,
                    decision="qualified" if decision.allowed else "rejected",
                    score=decision.score,
                    reason=decision.reason,
                )
                if not decision.allowed:
                    continue

                if should_dedupe(company.name, domain, existing_keys):
                    continue
                await create_lead(
                    session,
                    company_id=company.id,
                    region=company.region,
                    contact_email=None,
                    contact_status="pending",
                    status="new",
                )
                if company.name and domain:
                    existing_keys.add((" ".join(company.name.strip().lower().split()), domain.lower()))
                qualified += 1
                created += 1
            return {"qualified": qualified, "created": created, "total": len(companies)}

    import asyncio

    result = asyncio.run(_run())
    logger.info(
        "qualification_job_finished",
        total=result["total"],
        qualified=result["qualified"],
        created=result["created"],
    )

