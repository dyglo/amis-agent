from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5


@dataclass(frozen=True)
class TemplateVariant:
    subject_variants: list[str]
    body_template: str


PERSONA_TEMPLATES = {
    "Founder": TemplateVariant(
        subject_variants=[
            "Quick question about {company_name}",
            "Idea for {company_name}",
            "A quick idea for {company_name}",
        ],
        body_template=(
            "{first_line}\n\n"
            "{personalization_line}\n\n"
            "I help teams reduce manual work and respond faster with simple automation.\n"
            "Would a 10-minute demo this week be useful?\n"
        ),
    ),
    "CTO": TemplateVariant(
        subject_variants=[
            "Automation idea for {company_name}",
            "Technical quick win for {company_name}",
            "A practical automation win for {company_name}",
        ],
        body_template=(
            "{first_line}\n\n"
            "{personalization_line}\n\n"
            "I can share a practical automation win that is quick to implement.\n"
            "Open to a 10-minute technical walkthrough?\n"
        ),
    ),
    "Ops": TemplateVariant(
        subject_variants=[
            "Operations simplification for {company_name}",
            "Process improvement for {company_name}",
            "A quick ops improvement for {company_name}",
        ],
        body_template=(
            "{first_line}\n\n"
            "{personalization_line}\n\n"
            "I see an opportunity to streamline routine tasks and reduce overhead.\n"
            "Would a 10-minute demo be useful?\n"
        ),
    ),
}


def pick_persona(industry: str | None) -> str:
    if not industry:
        return "Founder"
    lowered = industry.lower()
    if "software" in lowered or "technology" in lowered:
        return "CTO"
    if "logistics" in lowered or "operations" in lowered:
        return "Ops"
    return "Founder"


def pick_subject_variant(company_name: str, persona: str) -> int:
    variants = PERSONA_TEMPLATES[persona].subject_variants
    if len(variants) == 1:
        return 0
    digest = md5(f"{company_name}:{persona}".encode("utf-8")).hexdigest()
    return int(digest, 16) % len(variants)
