import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard } from "../ChartCard";
import { StatTile } from "../StatTile";
import { categorical, chartChrome, ordinalBlueSteps, sequentialBlue } from "../../../lib/chartPalette";
import { axisTickStyle, legendStyle, tooltipContentStyle, tooltipLabelStyle } from "../chartTheme";
import { useAnalyticsQuery } from "../../../lib/useAnalyticsQuery";
import type { DashboardFilters, OperationsResponse } from "../../../lib/analyticsTypes";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function formatPeriod(period: string, granularity: string): string {
  const d = new Date(period);
  if (granularity === "month") return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function OperationsSection({ filters }: { filters: DashboardFilters }) {
  const { data, loading, error } = useAnalyticsQuery<OperationsResponse>("/analytics/operations", filters);

  const paymentMethods = (data?.payment_methods ?? []).map((p) => ({
    ...p,
    label: p.payment_type.replace(/_/g, " "),
  }));
  const reviewScores = (data?.review_scores ?? []).map((s) => ({ ...s, label: `${s.score} star` }));
  const ratingTrend = (data?.rating_trend ?? []).map((p) => ({
    ...p,
    label: formatPeriod(p.period, filters.granularity),
  }));

  return (
    <div className="space-y-6">
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile
          label="Avg. delivery time"
          value={data ? `${data.delivery.average_delivery_days ?? "-"} days` : "-"}
          loading={loading}
        />
        <StatTile
          label="On-time delivery rate"
          value={data ? `${data.delivery.on_time_rate ?? "-"}%` : "-"}
          loading={loading}
        />
        <StatTile
          label="Avg. review score"
          value={
            data && ratingTrend.length
              ? (ratingTrend.reduce((sum, p) => sum + p.average_score, 0) / ratingTrend.length).toFixed(2)
              : "-"
          }
          loading={loading}
        />
        <StatTile
          label="Payment methods used"
          value={data ? String(paymentMethods.length) : "-"}
          loading={loading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Payment method mix"
          description="Share of revenue by payment method"
          loading={loading}
          empty={!loading && paymentMethods.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={paymentMethods}
                dataKey="revenue"
                nameKey="label"
                innerRadius="55%"
                outerRadius="85%"
                paddingAngle={2}
              >
                {paymentMethods.map((_, i) => (
                  <Cell key={i} fill={categorical[i % categorical.length]} stroke="#ffffff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value) => currency.format(Number(value))}
              />
              <Legend wrapperStyle={legendStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Review score distribution"
          description="Count of reviews by star rating"
          loading={loading}
          empty={!loading && reviewScores.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={reviewScores} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={50} />
              <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
              <Bar dataKey="count" name="Reviews" radius={[4, 4, 0, 0]} maxBarSize={40}>
                {reviewScores.map((_, i) => (
                  <Cell key={i} fill={ordinalBlueSteps[i] ?? ordinalBlueSteps[ordinalBlueSteps.length - 1]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard
        title="Average rating over time"
        description={`Review score trend, ${filters.granularity}ly`}
        loading={loading}
        empty={!loading && ratingTrend.length === 0}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={ratingTrend} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
            <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
            <YAxis domain={[1, 5]} tick={axisTickStyle} axisLine={false} tickLine={false} width={30} />
            <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
            <Line
              type="monotone"
              dataKey="average_score"
              name="Avg. rating"
              stroke={sequentialBlue[500]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
