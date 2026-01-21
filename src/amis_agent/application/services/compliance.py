from __future__ import annotations

from dataclasses import dataclass

from amis_agent.core.constants import REGION_POLICY


def can_auto_send(region_code: str) -> bool:
    return REGION_POLICY.get(region_code, "opt_in_only") == "auto_send"


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reason: str | None = None


def evaluate_compliance(region_code: str | None, is_opt_in: bool) -> ComplianceDecision:
    if region_code is None:
        return ComplianceDecision(False, "missing_region")
    policy = REGION_POLICY.get(region_code, "opt_in_only")
    if policy == "auto_send":
        return ComplianceDecision(True)
    if policy == "opt_in_only" and is_opt_in:
        return ComplianceDecision(True)
    return ComplianceDecision(False, "opt_in_required")

