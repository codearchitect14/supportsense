import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.settings import settings
from app.db.session import get_db

logger = logging.getLogger("app.health")

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.limit(settings.rate_limit_default)
def health(request: Request) -> dict:
    return {"status": "ok"}


@router.get("/health/db")
@limiter.limit(settings.rate_limit_default)
def health_db(request: Request, db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("database health check failed")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unreachable") from exc
    return {"status": "ok", "database": "reachable"}
