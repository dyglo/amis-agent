from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from amis_agent.infrastructure.db.models import AuditLogModel


async def log_audit(
    session: AsyncSession,
    *,
    action: str,
    source: str | None = None,
    legal_basis: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLogModel:
    entry = AuditLogModel(
        action=action,
        source=source,
        legal_basis=legal_basis,
        details=json.dumps(details or {}),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
