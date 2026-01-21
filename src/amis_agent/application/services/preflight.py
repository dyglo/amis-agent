from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from amis_agent.application.services.email_render import has_unresolved_placeholders, render_email_body
from amis_agent.core.signature import EmailSignature, load_signature
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel


@dataclass(frozen=True)
class PreflightResult:
    allowed: bool
    details: dict[str, Any]


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _signature_valid(signature: EmailSignature) -> bool:
    return bool(signature.name and signature.title and signature.org)


def _source_url_valid(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def run_preflight(
    *,
    outbox: OutboxModel,
    lead: LeadModel,
    company: CompanyModel,
    signature: EmailSignature | None = None,
) -> PreflightResult:
    signature = signature or load_signature()
    rendered = render_email_body(body_text=outbox.body_text, signature=signature)

    details: dict[str, Any] = {
        "sender_email": None,
        "to_email": outbox.to_email,
        "subject_length": len(outbox.subject or ""),
        "word_count": _word_count(outbox.body_text),
        "placeholder_scan": not has_unresolved_placeholders(rendered)
        and not has_unresolved_placeholders(outbox.subject or ""),
        "signature_present": signature.render() in rendered,
        "signature_required_fields": _signature_valid(signature),
        "personalization_fact": outbox.personalization_fact,
        "personalization_source_url": outbox.personalization_source_url,
        "personalization_fact_in_body": bool(outbox.personalization_fact and outbox.personalization_fact in outbox.body_text),
        "status": outbox.status,
        "approved_by_human": outbox.approved_by_human,
    }

    allowed = True
    if not outbox.approved_by_human or outbox.status != "approved":
        allowed = False
    if not details["signature_required_fields"] or not details["signature_present"]:
        allowed = False
    if not details["placeholder_scan"]:
        allowed = False
    if details["word_count"] > 110:
        allowed = False
    if outbox.personalization_fact and not _source_url_valid(outbox.personalization_source_url):
        allowed = False
    if outbox.personalization_fact and not details["personalization_fact_in_body"]:
        allowed = False

    return PreflightResult(allowed=allowed, details=details)
