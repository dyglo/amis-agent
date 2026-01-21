from __future__ import annotations

from amis_agent.application.services.drafts import build_outbox_draft


def test_build_outbox_draft_contains_company():
    draft = build_outbox_draft(
        company_name="Acme Co",
        website_url="https://acme.example",
        persona="Founder",
        first_line=None,
    )
    assert "Acme Co" in draft.chosen_subject
    assert "https://acme.example" in draft.body_text
    assert draft.personalization_vars["company_name"] == "Acme Co"
    assert len(draft.subject_variants) == 3
