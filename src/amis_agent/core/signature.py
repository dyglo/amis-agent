from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EmailSignature:
    name: str
    title: str
    org: str
    website: str | None = None
    location: str | None = None

    def render(self) -> str:
        lines = [self.name, self.title, self.org]
        if self.website:
            lines.append(self.website)
        if self.location:
            lines.append(self.location)
        return "\n".join(lines)


def load_signature(path: str = "config/email_signature.txt") -> EmailSignature:
    data: dict[str, str] = {}
    content = Path(path).read_text(encoding="utf-8")
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    name = data.get("name", "")
    title = data.get("title", "")
    org = data.get("org", "")
    website = data.get("website") or None
    location = data.get("location") or None
    return EmailSignature(name=name, title=title, org=org, website=website, location=location)
