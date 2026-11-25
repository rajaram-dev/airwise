"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.deps import Services, build_services
from app.api.routes import router
from app.config import Settings, get_settings
from app.core.handlers import register_error_handlers
from app.core.logging import configure_logging
from app.core.security import limiter, security_middleware

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
USER_AGENT = f"AirWise/{__version__}"


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    """Build the app.

    Args:
        settings: Configuration; defaults to environment settings.
        services: Pre-built services (used by tests); real ones are created otherwise.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if services is not None:
            app.state.services = services
            yield
            return
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as http:
            app.state.services = build_services(settings, http)
            yield

    docs_url = "/docs" if settings.enable_docs else None
    app = FastAPI(
        title="AirWise API",
        version=__version__,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.state.limiter = limiter
    register_error_handlers(app)

    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.middleware("http")(security_middleware)

    app.include_router(router, prefix="/api/v1")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
