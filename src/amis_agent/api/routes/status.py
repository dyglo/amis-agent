from __future__ import annotations

from fastapi import APIRouter

from amis_agent.core.config import get_settings

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    settings = get_settings()
    return {
        "environment": settings.environment,
        "send_daily_limit": settings.send_daily_limit,
    }

