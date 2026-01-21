from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.api.deps import get_db_session, require_admin
from amis_agent.application.services.llm_email_writer import write_outbox_draft
from amis_agent.application.services.send_outbox import SendBlockedError, send_outbox_draft
from amis_agent.application.services.templates import pick_persona
from amis_agent.infrastructure.db.contact_repository import fetch_contacts_for_company
from amis_agent.infrastructure.db.models import (
    AuditLogModel,
    CompanyModel,
    ContactModel,
    LeadModel,
    OutboxModel,
)
from amis_agent.infrastructure.db.memory_repository import get_industry_insight
from amis_agent.infrastructure.queue.scheduler_store import SchedulerStore


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_db_session)) -> dict:
    company_count = await session.scalar(select(func.count()).select_from(CompanyModel)) or 0
    lead_counts = dict(
        (await session.execute(select(LeadModel.status, func.count()).group_by(LeadModel.status)))
        .all()
    )
    outbox_counts = dict(
        (await session.execute(select(OutboxModel.status, func.count()).group_by(OutboxModel.status)))
        .all()
    )
    audits = (
        await session.execute(
            select(AuditLogModel.action, AuditLogModel.source, AuditLogModel.created_at)
            .order_by(AuditLogModel.id.desc())
            .limit(10)
        )
    ).all()
    store = SchedulerStore()
    last_runs = {
        name: (store.get_last_run(name).isoformat() if store.get_last_run(name) else None)
        for name in ["discover", "qualify", "enrich", "outreach", "send_outbox"]
    }
    return {
        "companies": company_count,
        "leads_by_status": lead_counts,
        "outbox_by_status": outbox_counts,
        "last_runs": last_runs,
        "recent_activity": [
            {"action": a, "source": s, "created_at": c.isoformat()} for a, s, c in audits
        ],
    }


@router.get("/outbox")
async def list_outbox(
    status: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = (
        select(OutboxModel, LeadModel, CompanyModel)
        .join(LeadModel, OutboxModel.lead_id == LeadModel.id)
        .join(CompanyModel, LeadModel.company_id == CompanyModel.id)
        .order_by(OutboxModel.id.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(OutboxModel.status == status)
    rows = (await session.execute(stmt)).all()
    return {
        "items": [
            {
                "id": outbox.id,
                "status": outbox.status,
                "to_email": outbox.to_email,
                "subject": outbox.subject,
                "created_at": outbox.created_at.isoformat(),
                "approved_by_human": outbox.approved_by_human,
                "approved_by": outbox.approved_by,
                "lead_id": lead.id,
                "company_name": company.name,
            }
            for outbox, lead, company in rows
        ]
    }


@router.get("/outbox/{outbox_id}")
async def get_outbox(outbox_id: int, session: AsyncSession = Depends(get_db_session)) -> dict:
    stmt = (
        select(OutboxModel, LeadModel, CompanyModel, ContactModel)
        .join(LeadModel, OutboxModel.lead_id == LeadModel.id)
        .join(CompanyModel, LeadModel.company_id == CompanyModel.id)
        .outerjoin(ContactModel, LeadModel.contact_id == ContactModel.id)
        .where(OutboxModel.id == outbox_id)
    )
    row = (await session.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="outbox_not_found")
    outbox, lead, company, contact = row
    return {
        "id": outbox.id,
        "status": outbox.status,
        "to_email": outbox.to_email,
        "subject": outbox.subject,
        "subject_variants": outbox.subject_variants,
        "body_text": outbox.body_text,
        "followup_text": outbox.followup_text,
        "personalization_fact": outbox.personalization_fact,
        "personalization_source_url": outbox.personalization_source_url,
        "llm_model": outbox.llm_model,
        "llm_confidence": outbox.llm_confidence,
        "llm_rationale": outbox.llm_rationale,
        "created_at": outbox.created_at.isoformat(),
        "approved_by_human": outbox.approved_by_human,
        "approved_by": outbox.approved_by,
        "lead": {
            "id": lead.id,
            "contact_email": lead.contact_email,
            "contact_name": lead.contact_name,
            "contact_role": lead.contact_role,
            "status": lead.status,
        },
        "company": {
            "id": company.id,
            "name": company.name,
            "website_url": company.website_url,
            "industry": company.industry,
            "region": company.region,
        },
        "contact": {"id": contact.id, "email": contact.email} if contact else None,
    }


@router.post("/outbox/{outbox_id}/approve")
async def approve_outbox(outbox_id: int, session: AsyncSession = Depends(get_db_session)) -> dict:
    draft = (
        await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
    ).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="outbox_not_found")
    draft.status = "approved"
    draft.approved_by_human = True
    draft.approved_by = "Tafar M"
    draft.approved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "approved", "id": draft.id}


@router.post("/outbox/{outbox_id}/regenerate")
async def regenerate_outbox(outbox_id: int, session: AsyncSession = Depends(get_db_session)) -> dict:
    stmt = (
        select(OutboxModel, LeadModel, CompanyModel, ContactModel)
        .join(LeadModel, OutboxModel.lead_id == LeadModel.id)
        .join(CompanyModel, LeadModel.company_id == CompanyModel.id)
        .outerjoin(ContactModel, LeadModel.contact_id == ContactModel.id)
        .where(OutboxModel.id == outbox_id)
    )
    row = (await session.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="outbox_not_found")
    outbox, lead, company, contact = row
    await session.delete(outbox)
    await session.commit()
    if lead.status != "enriched":
        lead.status = "enriched"
        await session.commit()
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
    draft = await write_outbox_draft(
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
    return {"status": "ready_for_review", "id": draft.id}


@router.post("/outbox/{outbox_id}/send")
async def send_outbox(outbox_id: int, session: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        result = await send_outbox_draft(session, outbox_id)
    except SendBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": result.status, "response": result.response}


@router.post("/run/pipeline")
async def run_pipeline() -> dict:
    from amis_agent.application.services.jobs import (
        enqueue_discover,
        enqueue_enrich,
        enqueue_outreach,
        enqueue_qualify,
        enqueue_send_outbox,
    )

    jobs = [
        enqueue_discover(),
        enqueue_qualify(),
        enqueue_enrich(),
        enqueue_outreach(),
        enqueue_send_outbox(),
    ]
    return {"enqueued": [job.id for job in jobs if job is not None]}


@router.get("/companies")
async def list_companies(
    search: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(CompanyModel).order_by(CompanyModel.id.desc()).limit(limit)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(CompanyModel.name.ilike(like))
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "name": c.name,
                "industry": c.industry,
                "region": c.region,
                "website_url": c.website_url,
                "source": c.source,
                "created_at": c.created_at.isoformat(),
            }
            for c in rows
        ]
    }


@router.get("/leads")
async def list_leads(
    search: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = (
        select(LeadModel, CompanyModel)
        .join(CompanyModel, LeadModel.company_id == CompanyModel.id)
        .order_by(LeadModel.id.desc())
        .limit(limit)
    )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            LeadModel.contact_email.ilike(like) | CompanyModel.name.ilike(like)
        )
    rows = (await session.execute(stmt)).all()
    return {
        "items": [
            {
                "id": lead.id,
                "company_name": company.name,
                "contact_email": lead.contact_email,
                "contact_status": lead.contact_status,
                "status": lead.status,
                "created_at": lead.created_at.isoformat(),
            }
            for lead, company in rows
        ]
    }


@router.get("/settings")
async def settings_view() -> dict:
    from amis_agent.core.config import get_settings

    settings = get_settings()
    return {
        "enable_sending": settings.enable_sending,
        "s3_enabled": settings.s3_enabled,
        "gmail_sender": settings.gmail_sender,
    }
