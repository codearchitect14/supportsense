from datetime import date, datetime

from pydantic import BaseModel


class DateRangeFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    category: str | None = None


class KpiSummary(BaseModel):
    total_revenue: float
    total_orders: int
    average_order_value: float
    active_customers: int
    revenue_change_pct: float | None
    orders_change_pct: float | None
    aov_change_pct: float | None
    customers_change_pct: float | None


class TrendPoint(BaseModel):
    period: str
    revenue: float
    order_count: int


class CategoryBreakdown(BaseModel):
    category: str
    revenue: float
    order_count: int


class AovTrendPoint(BaseModel):
    period: str
    average_order_value: float


class CustomerGrowthPoint(BaseModel):
    period: str
    new_customers: int
    repeat_purchase_rate: float | None


class TopCustomer(BaseModel):
    customer_unique_id: str
    order_count: int
    total_spent: float


class OverviewResponse(BaseModel):
    kpis: KpiSummary
    revenue_trend: list[TrendPoint]
    category_breakdown: list[CategoryBreakdown]
    aov_trend: list[AovTrendPoint]


class CustomersResponse(BaseModel):
    growth: list[CustomerGrowthPoint]
    top_customers: list[TopCustomer]


class PaymentMethodShare(BaseModel):
    payment_type: str
    order_count: int
    revenue: float


class DeliveryMetrics(BaseModel):
    average_delivery_days: float | None
    on_time_rate: float | None


class ReviewScoreCount(BaseModel):
    score: int
    count: int


class RatingTrendPoint(BaseModel):
    period: str
    average_score: float


class OperationsResponse(BaseModel):
    payment_methods: list[PaymentMethodShare]
    delivery: DeliveryMetrics
    review_scores: list[ReviewScoreCount]
    rating_trend: list[RatingTrendPoint]


class ConversationVolumePoint(BaseModel):
    period: str
    count: int


class ProviderUsage(BaseModel):
    provider: str
    count: int


class SupportMetricsResponse(BaseModel):
    conversation_volume: list[ConversationVolumePoint]
    resolution_rate_pct: float | None
    provider_usage: list[ProviderUsage]
    average_tokens_per_conversation: float | None
    average_response_latency_seconds: float | None


class DataAvailability(BaseModel):
    min_order_date: datetime | None
    max_order_date: datetime | None
    categories: list[str]
