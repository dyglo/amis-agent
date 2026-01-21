from __future__ import annotations

from dataclasses import dataclass

from amis_agent.application.services.compliance import evaluate_compliance
from amis_agent.core.config import get_settings


@dataclass(frozen=True)
class EmailMessage:
    to_email: str
    subject: str
    body: str
    from_email: str
    from_name: str


class SuppressionStore:
    def is_suppressed(self, email: str) -> bool:
        raise NotImplementedError


def append_footer(body: str, footer: str) -> str:
    if not footer:
        return body
    if footer in body:
        return body
    return f"{body}\n\n{footer}"


def build_footer() -> str:
    settings = get_settings()
    if settings.footer_text:
        return settings.footer_text
    parts = [settings.email_display_name, settings.company_name, settings.footer_address]
    lines = [part for part in parts if part]
    return "\n".join(lines)


def prepare_message(to_email: str, subject: str, body: str) -> EmailMessage:
    settings = get_settings()
    footer = build_footer()
    full_body = append_footer(body, footer)
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        body=full_body,
        from_email=settings.email_from,
        from_name=settings.email_display_name,
    )


def enforce_compliance(
    *,
    to_email: str,
    region_code: str | None,
    is_opt_in: bool,
    suppression_store: SuppressionStore,
) -> None:
    if suppression_store.is_suppressed(to_email):
        raise ValueError("suppressed_email")
    decision = evaluate_compliance(region_code, is_opt_in)
    if not decision.allowed:
        raise ValueError(decision.reason or "compliance_block")

