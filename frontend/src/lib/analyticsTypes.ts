export interface KpiSummary {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  active_customers: number;
  revenue_change_pct: number | null;
  orders_change_pct: number | null;
  aov_change_pct: number | null;
  customers_change_pct: number | null;
}

export interface TrendPoint {
  period: string;
  revenue: number;
  order_count: number;
}

export interface CategoryBreakdown {
  category: string;
  revenue: number;
  order_count: number;
}

export interface AovTrendPoint {
  period: string;
  average_order_value: number;
}

export interface OverviewResponse {
  kpis: KpiSummary;
  revenue_trend: TrendPoint[];
  category_breakdown: CategoryBreakdown[];
  aov_trend: AovTrendPoint[];
}

export interface CustomerGrowthPoint {
  period: string;
  new_customers: number;
  repeat_purchase_rate: number | null;
}

export interface TopCustomer {
  customer_unique_id: string;
  order_count: number;
  total_spent: number;
}

export interface CustomersResponse {
  growth: CustomerGrowthPoint[];
  top_customers: TopCustomer[];
}

export interface PaymentMethodShare {
  payment_type: string;
  order_count: number;
  revenue: number;
}

export interface DeliveryMetrics {
  average_delivery_days: number | null;
  on_time_rate: number | null;
}

export interface ReviewScoreCount {
  score: number;
  count: number;
}

export interface RatingTrendPoint {
  period: string;
  average_score: number;
}

export interface OperationsResponse {
  payment_methods: PaymentMethodShare[];
  delivery: DeliveryMetrics;
  review_scores: ReviewScoreCount[];
  rating_trend: RatingTrendPoint[];
}

export interface ConversationVolumePoint {
  period: string;
  count: number;
}

export interface ProviderUsage {
  provider: string;
  count: number;
}

export interface SupportMetricsResponse {
  conversation_volume: ConversationVolumePoint[];
  resolution_rate_pct: number | null;
  provider_usage: ProviderUsage[];
  average_tokens_per_conversation: number | null;
  average_response_latency_seconds: number | null;
}

export interface DataAvailability {
  min_order_date: string | null;
  max_order_date: string | null;
  categories: string[];
}

export interface DashboardFilters {
  start_date?: string;
  end_date?: string;
  category?: string;
  granularity: "day" | "week" | "month";
}
