import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.core.settings import settings

configure_logging(settings.log_level)
logger = logging.getLogger("app.startup")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SupportSense API",
        version="0.1.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
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

    register_exception_handlers(app)

    app.include_router(api_router)

    logger.info("application configured", extra={"environment": settings.environment})

    return app


app = create_app()
