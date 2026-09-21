from datetime import date, datetime, timedelta

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

_VALID_GRANULARITY = {"day", "week", "month"}

# Orders that never completed shouldn't count as revenue.
_REVENUE_STATUS_EXCLUSIONS = ("canceled", "unavailable")


def _with_status_filter(sql: str):
    """A tuple bound to `:excluded_statuses` needs an expanding bindparam,
    or SQLAlchemy binds it as one scalar value instead of an IN (...) list.
    """
    return text(sql).bindparams(bindparam("excluded_statuses", expanding=True))


def _category_filter_clause(category: str | None) -> str:
    if not category:
        return ""
    return (
        "AND fo.order_id IN (SELECT foi.order_id FROM fact_order_items foi "
        "JOIN dim_products dp ON dp.product_id = foi.product_id "
        "WHERE dp.product_category_name = :category) "
    )


def _date_clause(prefix: str = "fo") -> str:
    return f"AND {prefix}.order_purchase_timestamp >= :start_date AND {prefix}.order_purchase_timestamp < :end_date "


def _granularity(value: str | None) -> str:
    return value if value in _VALID_GRANULARITY else "month"


def get_data_availability(db: Session, category: str | None = None) -> dict:
    row = (
        db.execute(
            text(
                "SELECT MIN(order_purchase_timestamp) AS min_date, MAX(order_purchase_timestamp) AS max_date FROM fact_orders"
            )
        )
        .mappings()
        .first()
    )
    categories = (
        db.execute(
            text(
                "SELECT DISTINCT product_category_name FROM dim_products "
                "WHERE product_category_name IS NOT NULL ORDER BY product_category_name"
            )
        )
        .scalars()
        .all()
    )
    return {"min_order_date": row["min_date"], "max_order_date": row["max_date"], "categories": categories}


def _effective_range(db: Session, start_date: date | None, end_date: date | None) -> tuple[datetime, datetime]:
    if start_date is None or end_date is None:
        bounds = (
            db.execute(
                text(
                    "SELECT MIN(order_purchase_timestamp) AS min_date, MAX(order_purchase_timestamp) AS max_date FROM fact_orders"
                )
            )
            .mappings()
            .first()
        )
        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else bounds["min_date"]
        end_dt = (
            datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
            if end_date
            else bounds["max_date"] + timedelta(days=1)
        )
    else:
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
    return start_dt, end_dt


def get_kpis(db: Session, start_date: date | None, end_date: date | None, category: str | None) -> dict:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    period_length = end_dt - start_dt
    prev_start_dt = start_dt - period_length
    prev_end_dt = start_dt

    def _summary(range_start: datetime, range_end: datetime) -> dict:
        query = _with_status_filter(
            "SELECT COUNT(DISTINCT fo.order_id) AS order_count, "
            "COALESCE(SUM(fp.payment_value), 0) AS revenue, "
            "COUNT(DISTINCT dc.customer_unique_id) AS active_customers "
            "FROM fact_orders fo "
            "JOIN dim_customers dc ON dc.customer_id = fo.customer_id "
            "LEFT JOIN fact_payments fp ON fp.order_id = fo.order_id "
            "WHERE fo.order_status NOT IN :excluded_statuses "
            "AND fo.order_purchase_timestamp >= :range_start AND fo.order_purchase_timestamp < :range_end "
            + _category_filter_clause(category)
        )
        params = {
            "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
            "range_start": range_start,
            "range_end": range_end,
        }
        if category:
            params["category"] = category
        return dict(db.execute(query, params).mappings().first())

    current = _summary(start_dt, end_dt)
    previous = _summary(prev_start_dt, prev_end_dt)

    current_revenue = float(current["revenue"])
    current_orders = int(current["order_count"])
    current_aov = current_revenue / current_orders if current_orders else 0.0
    current_customers = int(current["active_customers"])

    prev_revenue = float(previous["revenue"])
    prev_orders = int(previous["order_count"])
    prev_aov = prev_revenue / prev_orders if prev_orders else 0.0
    prev_customers = int(previous["active_customers"])

    def _pct_change(curr: float, prev: float) -> float | None:
        if prev == 0:
            return None
        return round((curr - prev) / prev * 100, 1)

    return {
        "total_revenue": round(current_revenue, 2),
        "total_orders": current_orders,
        "average_order_value": round(current_aov, 2),
        "active_customers": current_customers,
        "revenue_change_pct": _pct_change(current_revenue, prev_revenue),
        "orders_change_pct": _pct_change(current_orders, prev_orders),
        "aov_change_pct": _pct_change(current_aov, prev_aov),
        "customers_change_pct": _pct_change(current_customers, prev_customers),
    }


def get_revenue_trend(
    db: Session, start_date: date | None, end_date: date | None, category: str | None, granularity: str | None
) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    query = _with_status_filter(
        "SELECT date_trunc(:granularity, fo.order_purchase_timestamp) AS period, "
        "COALESCE(SUM(fp.payment_value), 0) AS revenue, COUNT(DISTINCT fo.order_id) AS order_count "
        "FROM fact_orders fo "
        "LEFT JOIN fact_payments fp ON fp.order_id = fo.order_id "
        "WHERE fo.order_status NOT IN :excluded_statuses "
        + _date_clause()
        + _category_filter_clause(category)
        + "GROUP BY period ORDER BY period"
    )
    params = {
        "granularity": _granularity(granularity),
        "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
        "start_date": start_dt,
        "end_date": end_dt,
    }
    if category:
        params["category"] = category
    rows = db.execute(query, params).mappings().all()
    return [
        {
            "period": row["period"].date().isoformat(),
            "revenue": float(row["revenue"]),
            "order_count": row["order_count"],
        }
        for row in rows
    ]


def get_category_breakdown(db: Session, start_date: date | None, end_date: date | None, limit: int = 12) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    query = _with_status_filter(
        "SELECT dp.product_category_name AS category, "
        "COALESCE(SUM(foi.price + foi.freight_value), 0) AS revenue, "
        "COUNT(DISTINCT fo.order_id) AS order_count "
        "FROM fact_order_items foi "
        "JOIN fact_orders fo ON fo.order_id = foi.order_id "
        "JOIN dim_products dp ON dp.product_id = foi.product_id "
        "WHERE fo.order_status NOT IN :excluded_statuses "
        "AND dp.product_category_name IS NOT NULL "
        + _date_clause()
        + "GROUP BY dp.product_category_name ORDER BY revenue DESC LIMIT :limit"
    )
    rows = (
        db.execute(
            query,
            {
                "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
                "start_date": start_dt,
                "end_date": end_dt,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )
    return [
        {"category": row["category"], "revenue": float(row["revenue"]), "order_count": row["order_count"]}
        for row in rows
    ]


def get_aov_trend(
    db: Session, start_date: date | None, end_date: date | None, category: str | None, granularity: str | None
) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    query = _with_status_filter(
        "SELECT date_trunc(:granularity, fo.order_purchase_timestamp) AS period, "
        "COALESCE(SUM(fp.payment_value), 0) / NULLIF(COUNT(DISTINCT fo.order_id), 0) AS aov "
        "FROM fact_orders fo "
        "LEFT JOIN fact_payments fp ON fp.order_id = fo.order_id "
        "WHERE fo.order_status NOT IN :excluded_statuses "
        + _date_clause()
        + _category_filter_clause(category)
        + "GROUP BY period ORDER BY period"
    )
    params = {
        "granularity": _granularity(granularity),
        "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
        "start_date": start_dt,
        "end_date": end_dt,
    }
    if category:
        params["category"] = category
    rows = db.execute(query, params).mappings().all()
    return [{"period": row["period"].date().isoformat(), "average_order_value": float(row["aov"] or 0)} for row in rows]


def get_customer_growth(
    db: Session, start_date: date | None, end_date: date | None, granularity: str | None
) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    # A customer's first-ever order (against their full history, not just
    # the filtered window) is what makes them "new" in a given period.
    query = _with_status_filter(
        "WITH first_orders AS ("
        "  SELECT dc.customer_unique_id, MIN(fo.order_purchase_timestamp) AS first_order_at, COUNT(*) AS lifetime_orders "
        "  FROM fact_orders fo JOIN dim_customers dc ON dc.customer_id = fo.customer_id "
        "  WHERE fo.order_status NOT IN :excluded_statuses "
        "  GROUP BY dc.customer_unique_id"
        ") "
        "SELECT date_trunc(:granularity, first_order_at) AS period, "
        "COUNT(*) AS new_customers, "
        "AVG(CASE WHEN lifetime_orders > 1 THEN 1.0 ELSE 0.0 END) AS repeat_rate "
        "FROM first_orders "
        "WHERE first_order_at >= :start_date AND first_order_at < :end_date "
        "GROUP BY period ORDER BY period"
    )
    rows = (
        db.execute(
            query,
            {
                "granularity": _granularity(granularity),
                "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
                "start_date": start_dt,
                "end_date": end_dt,
            },
        )
        .mappings()
        .all()
    )
    # A period with a handful of new customers makes the repeat rate pure
    # sampling noise (one repeat buyer in a 1-customer month reads as
    # "100% repeat rate"), which distorts the chart's whole scale. Report
    # volume regardless, but withhold the rate below a meaningful sample.
    _MIN_SAMPLE_FOR_RATE = 10
    return [
        {
            "period": row["period"].date().isoformat(),
            "new_customers": row["new_customers"],
            "repeat_purchase_rate": (
                round(float(row["repeat_rate"] or 0) * 100, 1) if row["new_customers"] >= _MIN_SAMPLE_FOR_RATE else None
            ),
        }
        for row in rows
    ]


def get_top_customers(db: Session, start_date: date | None, end_date: date | None, limit: int = 10) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    query = _with_status_filter(
        "SELECT dc.customer_unique_id, COUNT(DISTINCT fo.order_id) AS order_count, "
        "COALESCE(SUM(fp.payment_value), 0) AS total_spent "
        "FROM fact_orders fo "
        "JOIN dim_customers dc ON dc.customer_id = fo.customer_id "
        "LEFT JOIN fact_payments fp ON fp.order_id = fo.order_id "
        "WHERE fo.order_status NOT IN :excluded_statuses "
        + _date_clause()
        + "GROUP BY dc.customer_unique_id ORDER BY total_spent DESC LIMIT :limit"
    )
    rows = (
        db.execute(
            query,
            {
                "excluded_statuses": _REVENUE_STATUS_EXCLUSIONS,
                "start_date": start_dt,
                "end_date": end_dt,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )
    return [
        {
            "customer_unique_id": row["customer_unique_id"],
            "order_count": row["order_count"],
            "total_spent": float(row["total_spent"]),
        }
        for row in rows
    ]


def get_payment_methods(db: Session, start_date: date | None, end_date: date | None) -> list[dict]:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    query = _with_status_filter(
        "SELECT fp.payment_type, COUNT(DISTINCT fo.order_id) AS order_count, SUM(fp.payment_value) AS revenue "
        "FROM fact_payments fp JOIN fact_orders fo ON fo.order_id = fp.order_id "
        "WHERE fo.order_status NOT IN :excluded_statuses "
        + _date_clause()
        + "GROUP BY fp.payment_type ORDER BY revenue DESC"
    )
    rows = (
        db.execute(query, {"excluded_statuses": _REVENUE_STATUS_EXCLUSIONS, "start_date": start_dt, "end_date": end_dt})
        .mappings()
        .all()
    )
    return [
        {"payment_type": row["payment_type"], "order_count": row["order_count"], "revenue": float(row["revenue"] or 0)}
        for row in rows
    ]


def get_delivery_metrics(db: Session, start_date: date | None, end_date: date | None) -> dict:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    # The source data has a handful of rows with a corrupted
    # order_delivered_customer_date (e.g. year 48113), presumably an
    # upstream parsing error, that would otherwise blow the average up by
    # orders of magnitude. Cap the averaged window to a plausible delivery
    # time; on_time_rate is a simple date comparison and isn't affected.
    query = text(
        "SELECT AVG(EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400.0) "
        "  FILTER (WHERE order_delivered_customer_date - order_purchase_timestamp < INTERVAL '180 days') AS avg_days, "
        "AVG(CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 1.0 ELSE 0.0 END) AS on_time_rate "
        "FROM fact_orders fo "
        "WHERE order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NOT NULL "
        + _date_clause()
    )
    row = db.execute(query, {"start_date": start_dt, "end_date": end_dt}).mappings().first()
    avg_days = row["avg_days"]
    on_time = row["on_time_rate"]
    return {
        "average_delivery_days": round(float(avg_days), 1) if avg_days is not None else None,
        "on_time_rate": round(float(on_time) * 100, 1) if on_time is not None else None,
    }


def get_review_metrics(db: Session, start_date: date | None, end_date: date | None, granularity: str | None) -> dict:
    start_dt, end_dt = _effective_range(db, start_date, end_date)
    score_query = text(
        "SELECT fr.review_score AS score, COUNT(*) AS count FROM fact_reviews fr "
        "JOIN fact_orders fo ON fo.order_id = fr.order_id "
        "WHERE 1=1 " + _date_clause() + "GROUP BY fr.review_score ORDER BY fr.review_score"
    )
    score_rows = db.execute(score_query, {"start_date": start_dt, "end_date": end_dt}).mappings().all()

    trend_query = text(
        "SELECT date_trunc(:granularity, fo.order_purchase_timestamp) AS period, AVG(fr.review_score) AS avg_score "
        "FROM fact_reviews fr JOIN fact_orders fo ON fo.order_id = fr.order_id "
        "WHERE 1=1 " + _date_clause() + "GROUP BY period ORDER BY period"
    )
    trend_rows = (
        db.execute(trend_query, {"granularity": _granularity(granularity), "start_date": start_dt, "end_date": end_dt})
        .mappings()
        .all()
    )

    return {
        "review_scores": [{"score": row["score"], "count": row["count"]} for row in score_rows],
        "rating_trend": [
            {"period": row["period"].date().isoformat(), "average_score": round(float(row["avg_score"]), 2)}
            for row in trend_rows
        ],
    }


def get_support_metrics(db: Session, start_date: date | None, end_date: date | None, granularity: str | None) -> dict:
    date_clause = ""
    params: dict = {"granularity": _granularity(granularity)}
    if start_date:
        date_clause += "AND c.started_at >= :start_date "
        params["start_date"] = datetime.combine(start_date, datetime.min.time())
    if end_date:
        date_clause += "AND c.started_at < :end_date "
        params["end_date"] = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)

    volume_query = text(
        "SELECT date_trunc(:granularity, c.started_at) AS period, COUNT(*) AS count "
        "FROM conversations c WHERE 1=1 " + date_clause + "GROUP BY period ORDER BY period"
    )
    volume_rows = db.execute(volume_query, params).mappings().all()

    resolution_query = text(
        "SELECT "
        "COUNT(*) FILTER (WHERE m.role = 'user') AS user_turns, "
        "COUNT(*) FILTER (WHERE m.role = 'user' AND EXISTS ("
        "  SELECT 1 FROM messages reply WHERE reply.conversation_id = m.conversation_id "
        "  AND reply.role = 'assistant' AND reply.created_at > m.created_at"
        ")) AS resolved_turns "
        "FROM messages m JOIN conversations c ON c.id = m.conversation_id "
        "WHERE 1=1 " + date_clause
    )
    resolution_row = db.execute(resolution_query, params).mappings().first()
    user_turns = resolution_row["user_turns"] or 0
    resolved_turns = resolution_row["resolved_turns"] or 0
    resolution_rate = round(resolved_turns / user_turns * 100, 1) if user_turns else None

    provider_query = text(
        "SELECT m.provider_used AS provider, COUNT(*) AS count FROM messages m "
        "JOIN conversations c ON c.id = m.conversation_id "
        "WHERE m.role = 'assistant' AND m.provider_used IS NOT NULL "
        + date_clause
        + "GROUP BY m.provider_used ORDER BY count DESC"
    )
    provider_rows = db.execute(provider_query, params).mappings().all()

    tokens_query = text(
        "SELECT AVG(conv_tokens) AS avg_tokens FROM ("
        "  SELECT m.conversation_id, SUM(m.tokens_used) AS conv_tokens FROM messages m "
        "  JOIN conversations c ON c.id = m.conversation_id "
        "  WHERE m.role = 'assistant' " + date_clause + "GROUP BY m.conversation_id"
        ") sub"
    )
    avg_tokens = db.execute(tokens_query, params).scalar()

    latency_query = text(
        "SELECT AVG(EXTRACT(EPOCH FROM (a.created_at - u.created_at))) AS avg_latency "
        "FROM messages a "
        "JOIN LATERAL ("
        "  SELECT created_at FROM messages u2 WHERE u2.conversation_id = a.conversation_id "
        "  AND u2.role = 'user' AND u2.created_at < a.created_at ORDER BY u2.created_at DESC LIMIT 1"
        ") u ON true "
        "JOIN conversations c ON c.id = a.conversation_id "
        "WHERE a.role = 'assistant' " + date_clause
    )
    avg_latency = db.execute(latency_query, params).scalar()

    return {
        "conversation_volume": [
            {"period": row["period"].date().isoformat(), "count": row["count"]} for row in volume_rows
        ],
        "resolution_rate_pct": resolution_rate,
        "provider_usage": [{"provider": row["provider"], "count": row["count"]} for row in provider_rows],
        "average_tokens_per_conversation": round(float(avg_tokens), 1) if avg_tokens is not None else None,
        "average_response_latency_seconds": round(float(avg_latency), 2) if avg_latency is not None else None,
    }
