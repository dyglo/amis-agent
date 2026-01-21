from __future__ import annotations

from dataclasses import dataclass

from amis_agent.application.services.templates import PERSONA_TEMPLATES, pick_subject_variant


@dataclass(frozen=True)
class DraftMessage:
    subject_variants: list[str]
    chosen_subject: str
    body_text: str
    body_html: str | None
    personalization_vars: dict


def build_outbox_draft(
    *,
    company_name: str,
    website_url: str | None,
    persona: str,
    first_line: str | None,
    subject_variant: int | None = None,
    contact_name: str | None = None,
) -> DraftMessage:
    template = PERSONA_TEMPLATES[persona]
    variant = subject_variant if subject_variant is not None else pick_subject_variant(company_name, persona)
    if variant >= len(template.subject_variants):
        variant = variant % len(template.subject_variants)
    subject_variants = [s.format(company_name=company_name) for s in template.subject_variants]
    subject = subject_variants[variant]
    greeting_name = contact_name or company_name
    opening = first_line or f"Hello {greeting_name},"
    personalization_line = (
        first_line if first_line else f"I noticed your website at {website_url}."
    )
    body_text = template.body_template.format(
        first_line=opening,
        personalization_line=personalization_line,
    )
    return DraftMessage(
        subject_variants=subject_variants,
        chosen_subject=subject,
        body_text=body_text,
        body_html=None,
        personalization_vars={
            "company_name": company_name,
            "website_url": website_url,
            "persona": persona,
            "subject_variant": variant,
            "first_line": first_line,
        },
    )
