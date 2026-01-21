from __future__ import annotations

from fastapi import APIRouter

from amis_agent.api.routes.health import router as health_router
from amis_agent.api.routes.status import router as status_router
from amis_agent.api.routes.admin import router as admin_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(status_router, tags=["status"])
router.include_router(admin_router, tags=["admin"])

