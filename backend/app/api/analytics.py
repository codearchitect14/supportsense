import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    CustomersResponse,
    DataAvailability,
    OperationsResponse,
    OverviewResponse,
    SupportMetricsResponse,
)
from app.services import analytics_service
from app.services.audit_service import log_event

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _csv_response(filename: str, header: list[str], rows: list[list]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/availability", response_model=DataAvailability)
@limiter.limit("30/minute")
def availability(
    request: Request, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)
) -> DataAvailability:
    return DataAvailability(**analytics_service.get_data_availability(db))


@router.get("/overview", response_model=OverviewResponse)
@limiter.limit("30/minute")
def overview(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    granularity: str | None = Query(default="month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    log_event(db, user_id=current_user.id, action="analytics_access", resource="analytics:overview")
    return OverviewResponse(
        kpis=analytics_service.get_kpis(db, start_date, end_date, category),
        revenue_trend=analytics_service.get_revenue_trend(db, start_date, end_date, category, granularity),
        category_breakdown=analytics_service.get_category_breakdown(db, start_date, end_date),
        aov_trend=analytics_service.get_aov_trend(db, start_date, end_date, category, granularity),
    )


@router.get("/customers", response_model=CustomersResponse)
@limiter.limit("30/minute")
def customers(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str | None = Query(default="month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomersResponse:
    log_event(db, user_id=current_user.id, action="analytics_access", resource="analytics:customers")
    return CustomersResponse(
        growth=analytics_service.get_customer_growth(db, start_date, end_date, granularity),
        top_customers=analytics_service.get_top_customers(db, start_date, end_date),
    )


@router.get("/operations", response_model=OperationsResponse)
@limiter.limit("30/minute")
def operations(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str | None = Query(default="month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OperationsResponse:
    log_event(db, user_id=current_user.id, action="analytics_access", resource="analytics:operations")
    review_metrics = analytics_service.get_review_metrics(db, start_date, end_date, granularity)
    return OperationsResponse(
        payment_methods=analytics_service.get_payment_methods(db, start_date, end_date),
        delivery=analytics_service.get_delivery_metrics(db, start_date, end_date),
        review_scores=review_metrics["review_scores"],
        rating_trend=review_metrics["rating_trend"],
    )


@router.get("/support", response_model=SupportMetricsResponse)
@limiter.limit("30/minute")
def support(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str | None = Query(default="month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupportMetricsResponse:
    log_event(db, user_id=current_user.id, action="analytics_access", resource="analytics:support")
    return SupportMetricsResponse(**analytics_service.get_support_metrics(db, start_date, end_date, granularity))


@router.get("/export/revenue-trend.csv")
@limiter.limit("15/minute")
def export_revenue_trend(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    granularity: str | None = Query(default="month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    log_event(db, user_id=current_user.id, action="analytics_export", resource="analytics:revenue-trend.csv")
    rows = analytics_service.get_revenue_trend(db, start_date, end_date, category, granularity)
    return _csv_response(
        "revenue-trend.csv",
        ["period", "revenue", "order_count"],
        [[r["period"], r["revenue"], r["order_count"]] for r in rows],
    )


@router.get("/export/category-breakdown.csv")
@limiter.limit("15/minute")
def export_category_breakdown(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    log_event(db, user_id=current_user.id, action="analytics_export", resource="analytics:category-breakdown.csv")
    rows = analytics_service.get_category_breakdown(db, start_date, end_date, limit=1000)
    return _csv_response(
        "category-breakdown.csv",
        ["category", "revenue", "order_count"],
        [[r["category"], r["revenue"], r["order_count"]] for r in rows],
    )


@router.get("/export/top-customers.csv")
@limiter.limit("15/minute")
def export_top_customers(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    log_event(db, user_id=current_user.id, action="analytics_export", resource="analytics:top-customers.csv")
    rows = analytics_service.get_top_customers(db, start_date, end_date, limit=500)
    return _csv_response(
        "top-customers.csv",
        ["customer_unique_id", "order_count", "total_spent"],
        [[r["customer_unique_id"], r["order_count"], r["total_spent"]] for r in rows],
    )
