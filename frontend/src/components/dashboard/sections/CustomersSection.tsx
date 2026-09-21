import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard } from "../ChartCard";
import { Card } from "../../ui/Card";
import { sequentialBlue, chartChrome } from "../../../lib/chartPalette";
import { axisTickStyle, tooltipContentStyle, tooltipLabelStyle } from "../chartTheme";
import { useAnalyticsQuery, analyticsQueryString } from "../../../lib/useAnalyticsQuery";
import { API_BASE_URL } from "../../../lib/api";
import type { CustomersResponse, DashboardFilters } from "../../../lib/analyticsTypes";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function formatPeriod(period: string, granularity: string): string {
  const d = new Date(period);
  if (granularity === "month") return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function CustomersSection({ filters }: { filters: DashboardFilters }) {
  const { data, loading, error } = useAnalyticsQuery<CustomersResponse>("/analytics/customers", filters);

  const growth = (data?.growth ?? []).map((p) => ({ ...p, label: formatPeriod(p.period, filters.granularity) }));
  const topCustomers = data?.top_customers ?? [];

  return (
    <div className="space-y-6">
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="New customers"
          description={`New customers acquired, ${filters.granularity}ly`}
          loading={loading}
          empty={!loading && growth.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={growth} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={40} allowDecimals={false} />
              <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
              <Bar dataKey="new_customers" name="New customers" fill={sequentialBlue[400]} radius={[4, 4, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Repeat purchase rate"
          description="Share of new customers who go on to order again"
          loading={loading}
          empty={!loading && growth.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={growth} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis
                tick={axisTickStyle}
                axisLine={false}
                tickLine={false}
                width={44}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value) => [`${value}%`, "Repeat rate"]}
              />
              <Line
                type="monotone"
                dataKey="repeat_purchase_rate"
                name="Repeat rate"
                stroke={sequentialBlue[500]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Top customers by lifetime spend</h3>
          <a
            href={`${API_BASE_URL}/analytics/export/top-customers.csv?${analyticsQueryString(filters)}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-brand-300 hover:text-brand-700"
          >
            CSV
          </a>
        </div>

        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-9 w-full animate-pulse rounded bg-slate-100" />
            ))}
          </div>
        ) : topCustomers.length === 0 ? (
          <p className="text-sm text-slate-400">No customers for this filter selection.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-2">Customer</th>
                <th className="py-2 text-right">Orders</th>
                <th className="py-2 text-right">Total spent</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {topCustomers.map((c) => (
                <tr key={c.customer_unique_id}>
                  <td className="py-2.5 font-mono text-xs text-slate-600">{c.customer_unique_id.slice(0, 12)}…</td>
                  <td className="py-2.5 text-right text-slate-700">{c.order_count}</td>
                  <td className="py-2.5 text-right font-semibold text-slate-900">{currency.format(c.total_spent)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
