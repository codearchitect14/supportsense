import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "../../lib/cn";

export function StatTile({
  label,
  value,
  changePct,
  loading,
}: {
  label: string;
  value: string;
  changePct?: number | null;
  loading?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      {loading ? (
        <div className="mt-2 h-8 w-24 animate-pulse rounded bg-slate-100" />
      ) : (
        <p className="mt-1.5 font-heading text-2xl font-bold text-slate-900">{value}</p>
      )}
      {!loading && changePct !== undefined && changePct !== null && (
        <ChangeBadge changePct={changePct} />
      )}
    </div>
  );
}

function ChangeBadge({ changePct }: { changePct: number }) {
  const isFlat = Math.abs(changePct) < 0.05;
  const isUp = changePct > 0;
  const Icon = isFlat ? Minus : isUp ? TrendingUp : TrendingDown;

  return (
    <div
      className={cn(
        "mt-2 inline-flex items-center gap-1 text-xs font-semibold",
        isFlat ? "text-slate-400" : isUp ? "text-accent-600" : "text-red-500",
      )}
    >
      <Icon size={13} />
      {isFlat ? "flat" : `${isUp ? "+" : ""}${changePct}%`}
      <span className="font-normal text-slate-400">vs. prior period</span>
    </div>
  );
}
