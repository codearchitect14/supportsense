from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.core.settings import settings

# A dedicated reverse proxy or CDN in front of the deployed API should set
# these too (and is the more common place for them in production), but the
# API sets its own baseline so nothing depends on that layer being present.
_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# This API serves only JSON, except for Swagger/ReDoc, which are already
# disabled in production, so the strict CSP only needs to apply there.
_PRODUCTION_CSP = "default-src 'none'; frame-ancestors 'none'"


def register_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        for header, value in _HEADERS.items():
            response.headers.setdefault(header, value)
        if settings.is_production:
            response.headers.setdefault("Content-Security-Policy", _PRODUCTION_CSP)
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        return response
