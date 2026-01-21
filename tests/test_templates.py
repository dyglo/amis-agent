from __future__ import annotations

from amis_agent.application.services.templates import PERSONA_TEMPLATES, pick_persona, pick_subject_variant


def test_pick_persona_defaults():
    assert pick_persona(None) == "Founder"
    assert pick_persona("Technology") == "CTO"
    assert pick_persona("Operations") == "Ops"


def test_pick_subject_variant_is_deterministic():
    idx1 = pick_subject_variant("Acme Co", "Founder")
    idx2 = pick_subject_variant("Acme Co", "Founder")
    assert idx1 == idx2
    assert idx1 < len(PERSONA_TEMPLATES["Founder"].subject_variants)
