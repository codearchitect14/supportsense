def test_availability_reports_real_data_range(client, auth_headers):
    headers = auth_headers("analyticsuser1@example.com", role="viewer")
    response = client.get("/analytics/availability", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["min_order_date"] is not None
    assert body["max_order_date"] is not None
    assert len(body["categories"]) > 10


def test_overview_kpis_are_internally_consistent(client, auth_headers):
    headers = auth_headers("analyticsuser2@example.com", role="viewer")
    response = client.get("/analytics/overview", headers=headers)
    assert response.status_code == 200
    kpis = response.json()["kpis"]
    assert kpis["total_revenue"] > 0
    assert kpis["total_orders"] > 0
    assert abs(kpis["average_order_value"] - kpis["total_revenue"] / kpis["total_orders"]) < 0.01


def test_category_filter_narrows_kpis(client, auth_headers):
    headers = auth_headers("analyticsuser3@example.com", role="viewer")
    baseline = client.get("/analytics/overview", headers=headers).json()
    top_category = baseline["category_breakdown"][0]["category"]

    filtered = client.get("/analytics/overview", params={"category": top_category}, headers=headers).json()
    assert filtered["kpis"]["total_revenue"] < baseline["kpis"]["total_revenue"]
    assert filtered["kpis"]["total_revenue"] > 0


def test_delivery_metrics_are_sane_despite_known_data_outliers(client, auth_headers):
    """Regression test: a handful of source rows have a corrupted
    order_delivered_customer_date (year 48113), which once produced an
    average delivery time of ~500,000 days.
    """
    headers = auth_headers("analyticsuser4@example.com", role="viewer")
    response = client.get("/analytics/operations", headers=headers)
    delivery = response.json()["delivery"]
    assert delivery["average_delivery_days"] is not None
    assert 0 < delivery["average_delivery_days"] < 180
    assert 0 <= delivery["on_time_rate"] <= 100


def test_customer_growth_repeat_rate_withholds_low_sample_periods(client, auth_headers):
    """Regression test: a period with only 1-2 new customers made the
    repeat-purchase-rate axis read 0-100% instead of the real ~3-7% range.
    """
    headers = auth_headers("analyticsuser5@example.com", role="viewer")
    response = client.get("/analytics/customers", headers=headers)
    growth = response.json()["growth"]
    assert len(growth) > 0
    for point in growth:
        if point["new_customers"] < 10:
            assert point["repeat_purchase_rate"] is None


def test_support_metrics_reflect_a_real_conversation(client, auth_headers, kb_query):
    headers = auth_headers("analyticsuser6@example.com")
    client.post("/chat/message", json={"message": kb_query}, headers=headers)

    response = client.get("/analytics/support", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert sum(p["count"] for p in body["conversation_volume"]) >= 1
    assert body["resolution_rate_pct"] == 100.0
    assert any(p["provider"] == "kb_direct" for p in body["provider_usage"])


def test_csv_export_has_expected_header_and_rows(client, auth_headers):
    headers = auth_headers("analyticsuser7@example.com", role="viewer")
    response = client.get("/analytics/export/revenue-trend.csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    lines = response.text.splitlines()
    assert lines[0] == "period,revenue,order_count"
    assert len(lines) > 1


def test_analytics_access_is_audit_logged(client, auth_headers, db_session):
    from app.models.audit import AuditLog

    headers = auth_headers("analyticsaudit@example.com", role="viewer")
    client.get("/analytics/overview", headers=headers)

    logged = db_session.query(AuditLog).filter(AuditLog.action == "analytics_access").all()
    assert any(entry.resource == "analytics:overview" for entry in logged)
