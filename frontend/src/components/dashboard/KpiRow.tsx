import { StatTile } from "./StatTile";
import type { KpiSummary } from "../../lib/analyticsTypes";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("en-US");

export function KpiRow({ kpis, loading }: { kpis: KpiSummary | null; loading: boolean }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatTile
        label="Total revenue"
        value={kpis ? currency.format(kpis.total_revenue) : "—"}
        changePct={kpis?.revenue_change_pct}
        loading={loading}
      />
      <StatTile
        label="Total orders"
        value={kpis ? number.format(kpis.total_orders) : "—"}
        changePct={kpis?.orders_change_pct}
        loading={loading}
      />
      <StatTile
        label="Average order value"
        value={kpis ? currency.format(kpis.average_order_value) : "—"}
        changePct={kpis?.aov_change_pct}
        loading={loading}
      />
      <StatTile
        label="Active customers"
        value={kpis ? number.format(kpis.active_customers) : "—"}
        changePct={kpis?.customers_change_pct}
        loading={loading}
      />
    </div>
  );
}
