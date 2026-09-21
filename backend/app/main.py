import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.core.security_headers import register_security_headers
from app.core.settings import settings
from app.services.embedding_service import get_embedding_service
from app.services.stt_service import get_stt_service

configure_logging(settings.log_level)
logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loads the embedding and speech-to-text models once at startup rather
    # than on the first request, so the first real user doesn't pay the
    # load latency.
    get_embedding_service()
    get_stt_service()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SupportSense API",
        version="0.1.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": {"code": "rate_limited", "message": "too many requests", "details": None}},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)

    register_security_headers(app)
    register_exception_handlers(app)

    app.include_router(api_router)

    logger.info("application configured", extra={"environment": settings.environment})

    return app


app = create_app()
