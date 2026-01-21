from __future__ import annotations

import pytest

from amis_agent.application.services.lead_pipeline import assert_transition, can_transition


def test_can_transition_happy_path():
    assert can_transition("new", "enriched") is True
    assert can_transition("enriched", "ready_for_review") is True


def test_assert_transition_blocks_invalid():
    with pytest.raises(ValueError):
        assert_transition("new", "sent")
