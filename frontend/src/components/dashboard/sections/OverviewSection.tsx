import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard } from "../ChartCard";
import { KpiRow } from "../KpiRow";
import { sequentialBlue, chartChrome } from "../../../lib/chartPalette";
import { axisTickStyle, tooltipContentStyle, tooltipLabelStyle } from "../chartTheme";
import { useAnalyticsQuery, analyticsQueryString } from "../../../lib/useAnalyticsQuery";
import { API_BASE_URL } from "../../../lib/api";
import type { DashboardFilters, OverviewResponse } from "../../../lib/analyticsTypes";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function formatPeriod(period: string, granularity: string): string {
  const d = new Date(period);
  if (granularity === "month") return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function OverviewSection({ filters }: { filters: DashboardFilters }) {
  const { data, loading, error } = useAnalyticsQuery<OverviewResponse>("/analytics/overview", filters);

  const revenueTrend = (data?.revenue_trend ?? []).map((p) => ({
    ...p,
    label: formatPeriod(p.period, filters.granularity),
  }));
  const aovTrend = (data?.aov_trend ?? []).map((p) => ({
    ...p,
    label: formatPeriod(p.period, filters.granularity),
  }));
  const categories = (data?.category_breakdown ?? []).slice(0, 10).map((c) => ({
    ...c,
    label: c.category.replace(/_/g, " "),
  }));

  return (
    <div className="space-y-6">
      <KpiRow kpis={data?.kpis ?? null} loading={loading} />
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Revenue over time"
          description={`Total revenue, ${filters.granularity}ly`}
          loading={loading}
          empty={!loading && revenueTrend.length === 0}
          exportHref={`${API_BASE_URL}/analytics/export/revenue-trend.csv?${analyticsQueryString(filters)}`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={revenueTrend} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis
                tick={axisTickStyle}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => currency.format(v)}
                width={70}
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value) => [currency.format(Number(value)), "Revenue"]}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke={sequentialBlue[500]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Average order value"
          description={`AOV trend, ${filters.granularity}ly`}
          loading={loading}
          empty={!loading && aovTrend.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={aovTrend} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis
                tick={axisTickStyle}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => currency.format(v)}
                width={70}
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value) => [currency.format(Number(value)), "AOV"]}
              />
              <Line
                type="monotone"
                dataKey="average_order_value"
                name="AOV"
                stroke={sequentialBlue[500]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard
        title="Revenue by product category"
        description="Top 10 categories by revenue"
        loading={loading}
        empty={!loading && categories.length === 0}
        height={360}
        exportHref={`${API_BASE_URL}/analytics/export/category-breakdown.csv?${analyticsQueryString(filters)}`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={categories} layout="vertical" margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={chartChrome.gridline} horizontal={false} />
            <XAxis
              type="number"
              tick={axisTickStyle}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => currency.format(v)}
            />
            <YAxis
              type="category"
              dataKey="label"
              tick={axisTickStyle}
              axisLine={false}
              tickLine={false}
              width={140}
            />
            <Tooltip
              contentStyle={tooltipContentStyle}
              labelStyle={tooltipLabelStyle}
              formatter={(value) => [currency.format(Number(value)), "Revenue"]}
            />
            <Bar dataKey="revenue" name="Revenue" fill={sequentialBlue[400]} radius={[0, 4, 4, 0]} maxBarSize={22} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
