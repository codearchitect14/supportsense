import type { ReactNode } from "react";
import { Download, Inbox } from "lucide-react";
import { Card } from "../ui/Card";

export function ChartCard({
  title,
  description,
  loading,
  empty,
  height = 280,
  exportHref,
  children,
}: {
  title: string;
  description?: string;
  loading?: boolean;
  empty?: boolean;
  height?: number;
  exportHref?: string;
  children: ReactNode;
}) {
  return (
    <Card className="flex flex-col">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
        </div>
        {exportHref && !loading && !empty && (
          <a
            href={exportHref}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-brand-300 hover:text-brand-700"
          >
            <Download size={13} />
            CSV
          </a>
        )}
      </div>

      <div style={{ height }} className="relative">
        {loading ? (
          <ChartSkeleton />
        ) : empty ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Inbox className="mb-2 text-slate-300" size={26} />
            <p className="text-sm text-slate-400">No data for this filter selection.</p>
          </div>
        ) : (
          children
        )}
      </div>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <div className="flex h-full items-end gap-2 px-2 pb-2">
      {[40, 65, 45, 80, 55, 70, 50, 85, 60].map((h, i) => (
        <div
          key={i}
          className="flex-1 animate-pulse rounded-t-sm bg-slate-100"
          style={{ height: `${h}%` }}
        />
      ))}
    </div>
  );
}
