from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Company:
    name: str
    industry: Optional[str]
    region: Optional[str]
    website_status: Optional[str]


@dataclass(frozen=True)
class Lead:
    company_name: str
    contact_email: Optional[str]
    contact_name: Optional[str]
    region: Optional[str]

