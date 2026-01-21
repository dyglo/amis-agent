from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from amis_agent.api.routes import router as api_router
from amis_agent.core.config import get_settings
from amis_agent.core.logging import configure_logging, get_logger
from amis_agent.core.metrics import setup_metrics


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(service="api")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("startup", environment=settings.environment)
        yield
        logger.info("shutdown")

    app = FastAPI(title="AMIS Digital Me Agent", version="0.1.0", lifespan=lifespan)
    setup_metrics(app)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

