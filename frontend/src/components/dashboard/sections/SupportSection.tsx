import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard } from "../ChartCard";
import { StatTile } from "../StatTile";
import { categorical, chartChrome, sequentialBlue } from "../../../lib/chartPalette";
import { axisTickStyle, legendStyle, tooltipContentStyle, tooltipLabelStyle } from "../chartTheme";
import { useAnalyticsQuery } from "../../../lib/useAnalyticsQuery";
import type { DashboardFilters, SupportMetricsResponse } from "../../../lib/analyticsTypes";

const providerLabels: Record<string, string> = {
  groq: "Groq",
  gemini: "Gemini",
  kb_direct: "Knowledge base",
  cache: "Cached answer",
};

function formatPeriod(period: string, granularity: string): string {
  const d = new Date(period);
  if (granularity === "month") return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function SupportSection({ filters }: { filters: DashboardFilters }) {
  const { data, loading, error } = useAnalyticsQuery<SupportMetricsResponse>("/analytics/support", filters);

  const volume = (data?.conversation_volume ?? []).map((p) => ({
    ...p,
    label: formatPeriod(p.period, filters.granularity),
  }));
  const providerUsage = (data?.provider_usage ?? []).map((p) => ({
    ...p,
    label: providerLabels[p.provider] ?? p.provider,
  }));

  return (
    <div className="space-y-6">
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatTile
          label="Resolved without escalation"
          value={data?.resolution_rate_pct != null ? `${data.resolution_rate_pct}%` : "—"}
          loading={loading}
        />
        <StatTile
          label="Avg. tokens per conversation"
          value={data?.average_tokens_per_conversation != null ? String(data.average_tokens_per_conversation) : "—"}
          loading={loading}
        />
        <StatTile
          label="Avg. response latency"
          value={data?.average_response_latency_seconds != null ? `${data.average_response_latency_seconds}s` : "—"}
          loading={loading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Conversation volume"
          description={`Conversations started, ${filters.granularity}ly`}
          loading={loading}
          empty={!loading && volume.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={volume} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartChrome.gridline} vertical={false} />
              <XAxis dataKey="label" tick={axisTickStyle} axisLine={{ stroke: chartChrome.axis }} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={36} allowDecimals={false} />
              <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
              <Bar dataKey="count" name="Conversations" fill={sequentialBlue[400]} radius={[4, 4, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="LLM provider usage"
          description="Which provider answered each conversation"
          loading={loading}
          empty={!loading && providerUsage.length === 0}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={providerUsage} dataKey="count" nameKey="label" innerRadius="55%" outerRadius="85%" paddingAngle={2}>
                {providerUsage.map((_, i) => (
                  <Cell key={i} fill={categorical[i % categorical.length]} stroke="#ffffff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
              <Legend wrapperStyle={legendStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
