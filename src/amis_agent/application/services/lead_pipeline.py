from __future__ import annotations


LEAD_STATUS_FLOW = {
    "new": {"enriched"},
    "enriched": {"ready_for_review"},
    "ready_for_review": {"approved"},
    "approved": {"sent"},
}


def can_transition(current: str, target: str) -> bool:
    return target in LEAD_STATUS_FLOW.get(current, set())


def assert_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        raise ValueError(f"invalid_transition:{current}->{target}")
