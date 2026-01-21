from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class QualificationDecision:
    allowed: bool
    score: int
    reason: str | None = None


def normalize_company_name(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).hostname or ""
    return host.lower() or None


def qualify_company(
    *,
    name: str | None,
    website_status: str | None,
    website_url: str | None,
    region: str | None,
    source: str | None,
    allowed_sources: set[str],
    allowed_domains: set[str],
) -> QualificationDecision:
    normalized = normalize_company_name(name)
    if not normalized:
        return QualificationDecision(False, 0, "missing_name")

    if website_status != "has_website":
        return QualificationDecision(False, 10, "missing_website")

    domain = extract_domain(website_url)
    if allowed_domains and (domain is None or domain not in allowed_domains):
        return QualificationDecision(False, 20, "domain_not_allowed")

    if allowed_sources and (source is None or source not in allowed_sources):
        return QualificationDecision(False, 20, "source_not_allowed")

    score = 50
    if domain:
        score += 20
    if region:
        score += 10
    if source:
        score += 10
    return QualificationDecision(True, min(score, 100), None)


def should_dedupe(company_name: str, website_domain: str | None, existing_keys: set[tuple[str, str]]) -> bool:
    if not company_name or not website_domain:
        return False
    key = (normalize_company_name(company_name), website_domain.lower())
    return key in existing_keys
