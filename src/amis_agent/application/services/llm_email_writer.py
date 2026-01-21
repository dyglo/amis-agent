from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from amis_agent.application.services.drafts import build_outbox_draft
from amis_agent.application.services.templates import pick_persona
from amis_agent.core.config import get_settings
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.db.models import CompanyModel, ContactModel, LeadModel, OutboxModel
from amis_agent.infrastructure.db.outbox_repository import create_llm_draft, fetch_existing_draft
from amis_agent.infrastructure.db.audit_repository import log_audit
from amis_agent.infrastructure.llm.client import LLMClient


logger = get_logger(service="llm_email_writer")


@dataclass(frozen=True)
class LLMEmailInput:
    lead: LeadModel
    company: CompanyModel
    contact: ContactModel | None
    snippets: dict
    value_props: list[str]
    persona: str
    tone: str


@dataclass(frozen=True)
class LLMEmailOutput:
    subject_variants: list[str]
    chosen_subject: str
    body_text: str
    followup_text: str
    personalization_fields: dict
    personalization_fact: str | None
    personalization_source_url: str | None
    confidence: float
    rationale: str


def _prompt_payload(data: LLMEmailInput) -> dict:
    return {
        "company": {
            "name": data.company.name,
            "industry": data.company.industry,
            "region": data.company.region,
            "website_url": data.company.website_url,
        },
        "lead": {
            "contact_name": data.lead.contact_name,
            "contact_role": data.lead.contact_role,
            "contact_email": data.lead.contact_email,
        },
        "contact": {"email": data.contact.email if data.contact else None},
        "snippets": data.snippets,
        "value_props": data.value_props,
        "persona": data.persona,
        "tone": data.tone,
        "constraints": {"max_words": 110, "subject_variants": 3},
        "output_format": {
            "subject_variants": ["..."],
            "chosen_subject": "...",
            "body_text": "...",
            "followup_text": "...",
            "personalization_fields": {"company_name": "..."},
            "personalization_fact": "...",
            "personalization_source_url": "...",
            "confidence": 0.0,
            "rationale": "...",
        },
    }


def _hash_prompt(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _fallback(data: LLMEmailInput) -> LLMEmailOutput:
    persona = data.persona or pick_persona(data.company.industry)
    draft = build_outbox_draft(
        company_name=data.company.name,
        website_url=data.company.website_url,
        persona=persona,
        first_line=data.snippets.get("about"),
        contact_name=data.lead.contact_name,
    )
    return LLMEmailOutput(
        subject_variants=draft.subject_variants,
        chosen_subject=draft.chosen_subject,
        body_text=draft.body_text,
        followup_text="Just checking if a quick 10-minute chat this week works.",
        personalization_fields=draft.personalization_vars,
        personalization_fact=data.snippets.get("about") or f"Has a website at {data.company.website_url}",
        personalization_source_url=data.company.website_url,
        confidence=0.35,
        rationale="fallback_template",
    )


_PLACEHOLDER_RE = re.compile(r"\[[^\]]+\]|\{\{[^}]+\}\}")


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _validate_output(output: LLMEmailOutput) -> bool:
    if len(output.subject_variants) != 3:
        return False
    if output.chosen_subject not in output.subject_variants:
        return False
    if _word_count(output.body_text) > 110:
        return False
    if _PLACEHOLDER_RE.search(output.body_text):
        return False
    if not output.personalization_fact:
        return False
    if not output.personalization_source_url:
        return False
    return True


def _parse_json_content(content: str) -> dict:
    trimmed = content.strip()
    if trimmed.startswith("{") and trimmed.endswith("}"):
        return json.loads(trimmed)
    start = trimmed.find("{")
    end = trimmed.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(trimmed[start : end + 1])
    return json.loads(trimmed)


class LLMEmailWriter:
    def __init__(self, client: LLMClient | None = None) -> None:
        settings = get_settings()
        self.client = client or LLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout_s=settings.llm_timeout,
        )
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens

    def generate(
        self, data: LLMEmailInput
    ) -> tuple[LLMEmailOutput, str, dict | None, int | None, str | None]:
        payload = _prompt_payload(data)
        prompt_hash = _hash_prompt(payload)
        system = (
            "You are an outreach copywriter. Return ONLY valid JSON matching output_format. "
            "Do not include markdown or commentary. Use <=110 words. Provide 3 subject variants. "
            "Use a neutral greeting if no contact name is provided. Include exactly one personalization line "
            "based on a verified fact and include its source URL in personalization_source_url."
        )
        user = json.dumps(payload, ensure_ascii=False)
        try:
            response = self.client.create_chat_completion(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=self.max_tokens,
            )
            parsed = _parse_json_content(response.content)
            output = LLMEmailOutput(
                subject_variants=parsed["subject_variants"],
                chosen_subject=parsed["chosen_subject"],
                body_text=parsed["body_text"],
                followup_text=parsed["followup_text"],
                personalization_fields=parsed.get("personalization_fields", {}),
                personalization_fact=parsed.get("personalization_fact"),
                personalization_source_url=parsed.get("personalization_source_url"),
                confidence=float(parsed.get("confidence", 0.5)),
                rationale=parsed.get("rationale", ""),
            )
            if not _validate_output(output):
                return _fallback(data), prompt_hash, response.usage, response.latency_ms, "validation_failed"
            return output, prompt_hash, response.usage, response.latency_ms, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_generate_failed", error=str(exc))
            return _fallback(data), prompt_hash, None, None, str(exc)


async def write_outbox_draft(
    session,
    *,
    lead: LeadModel,
    company: CompanyModel,
    contact: ContactModel | None,
    snippets: dict,
    value_props: list[str],
    persona: str,
    tone: str,
    status: str = "ready_for_review",
) -> OutboxModel:
    data = LLMEmailInput(
        lead=lead,
        company=company,
        contact=contact,
        snippets=snippets,
        value_props=value_props,
        persona=persona,
        tone=tone,
    )
    payload = _prompt_payload(data)
    prompt_hash = _hash_prompt(payload)

    existing = await fetch_existing_draft(session, lead_id=lead.id)
    if existing:
        return existing
    writer = LLMEmailWriter()
    output, prompt_hash, usage, latency_ms, error = writer.generate(data)

    await log_audit(
        session,
        action="llm_draft",
        source="llm_email_writer",
        details={
            "prompt_hash": prompt_hash,
            "model": writer.model,
            "latency_ms": latency_ms,
            "usage": usage,
            "error": error or (None if output.rationale != "fallback_template" else "fallback_template"),
        },
    )

    return await create_llm_draft(
        session,
        lead_id=lead.id,
        to_email=lead.contact_email,
        subject=output.chosen_subject,
        subject_variants=output.subject_variants,
        body_text=output.body_text,
        body_html=None,
        followup_text=output.followup_text,
        personalization_vars=output.personalization_fields,
        personalization_fact=output.personalization_fact,
        personalization_source_url=output.personalization_source_url,
        prompt_hash=prompt_hash,
        llm_model=writer.model,
        llm_latency_ms=latency_ms,
        llm_token_usage=usage,
        llm_confidence=output.confidence,
        llm_rationale=output.rationale,
        status=status,
    )
