from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import OutboxModel


async def create_draft(
    session: AsyncSession,
    *,
    lead_id: int,
    to_email: str | None,
    subject: str,
    body_text: str,
    body_html: str | None,
    personalization_vars: dict,
) -> OutboxModel:
    stmt = (
        select(OutboxModel)
        .where(OutboxModel.lead_id == lead_id)
        .where(OutboxModel.status == "draft")
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing

    draft = OutboxModel(
        lead_id=lead_id,
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        personalization_vars=personalization_vars,
        status="draft",
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft


async def fetch_existing_draft(session: AsyncSession, *, lead_id: int) -> OutboxModel | None:
    stmt = (
        select(OutboxModel)
        .where(OutboxModel.lead_id == lead_id)
        .where(OutboxModel.status.in_(["draft", "ready_for_review"]))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def create_llm_draft(
    session: AsyncSession,
    *,
    lead_id: int,
    to_email: str | None,
    subject: str,
    subject_variants: list[str],
    body_text: str,
    body_html: str | None,
    followup_text: str | None,
    personalization_vars: dict,
    personalization_fact: str | None,
    personalization_source_url: str | None,
    prompt_hash: str,
    llm_model: str,
    llm_latency_ms: int | None,
    llm_token_usage: dict | None,
    llm_confidence: float | None,
    llm_rationale: str | None,
    status: str,
) -> OutboxModel:
    draft = OutboxModel(
        lead_id=lead_id,
        to_email=to_email,
        subject=subject,
        subject_variants=subject_variants,
        body_text=body_text,
        body_html=body_html,
        followup_text=followup_text,
        personalization_vars=personalization_vars,
        personalization_fact=personalization_fact,
        personalization_source_url=personalization_source_url,
        prompt_hash=prompt_hash,
        llm_model=llm_model,
        llm_latency_ms=llm_latency_ms,
        llm_token_usage=llm_token_usage,
        llm_confidence=llm_confidence,
        llm_rationale=llm_rationale,
        status=status,
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft


async def fetch_approved(session: AsyncSession, limit: int = 10) -> list[OutboxModel]:
    stmt = (
        select(OutboxModel)
        .where(OutboxModel.status == "approved")
        .where(OutboxModel.approved_by_human.is_(True))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def mark_sent(session: AsyncSession, draft: OutboxModel) -> OutboxModel:
    draft.status = "sent"
    await session.commit()
    await session.refresh(draft)
    return draft
