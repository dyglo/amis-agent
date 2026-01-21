from __future__ import annotations

import re

from amis_agent.core.signature import EmailSignature


COMPLIANCE_FOOTER = "If I reached the wrong person, reply 'no' and I won't follow up."
_PLACEHOLDER_RE = re.compile(r"\[[^\]]+\]|\{\{[^}]+\}\}")


def render_email_body(*, body_text: str, signature: EmailSignature) -> str:
    signature_text = signature.render()
    return f"{body_text}\n\n{signature_text}\n\n{COMPLIANCE_FOOTER}"


def has_unresolved_placeholders(text: str) -> bool:
    return _PLACEHOLDER_RE.search(text) is not None
