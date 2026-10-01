import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from APP.API.v1.router import router
from APP.core.config import Settings, get_settings
from APP.core.db import create_engine, create_session_factory
from APP.core.logging import configure_logging
from APP.core.security import dummy_password_hash
from APP.core.storage import create_storage
from APP.core.upload_limit import UploadLimitMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    configure_logging(settings.log_level)
    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.storage = None
    try:
        app.state.storage = create_storage(settings)
        await run_in_threadpool(dummy_password_hash, settings.bcrypt_rounds)
        logger.info("Application started")
        yield
    finally:
        if app.state.storage is not None:
            await run_in_threadpool(app.state.storage.close)
        await engine.dispose()
        logger.info("Application stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        swagger_ui_oauth2_redirect_url="/api/v1/docs/oauth2-redirect",
    )
    app.add_middleware(UploadLimitMiddleware, settings=settings)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin).rstrip("/") for origin in settings.cors_origins],
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    app.state.settings = settings
    app.include_router(router)
    return app
