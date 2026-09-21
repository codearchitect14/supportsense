import { useEffect, useState } from "react";
import { Filter } from "lucide-react";
import { Input } from "../ui/Input";
import { api } from "../../lib/api";
import type { DashboardFilters, DataAvailability } from "../../lib/analyticsTypes";

export function FiltersBar({
  filters,
  onChange,
}: {
  filters: DashboardFilters;
  onChange: (filters: DashboardFilters) => void;
}) {
  const [availability, setAvailability] = useState<DataAvailability | null>(null);

  useEffect(() => {
    api.get<DataAvailability>("/analytics/availability").then(setAvailability).catch(() => {});
  }, []);

  const minDate = availability?.min_order_date?.slice(0, 10);
  const maxDate = availability?.max_order_date?.slice(0, 10);

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-4">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
        <Filter size={13} />
        Filters
      </div>

      <Input
        type="date"
        value={filters.start_date ?? ""}
        min={minDate}
        max={maxDate}
        onChange={(e) => onChange({ ...filters, start_date: e.target.value || undefined })}
        className="w-auto"
        aria-label="Start date"
      />
      <span className="text-sm text-slate-400">to</span>
      <Input
        type="date"
        value={filters.end_date ?? ""}
        min={minDate}
        max={maxDate}
        onChange={(e) => onChange({ ...filters, end_date: e.target.value || undefined })}
        className="w-auto"
        aria-label="End date"
      />

      <select
        value={filters.category ?? ""}
        onChange={(e) => onChange({ ...filters, category: e.target.value || undefined })}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
      >
        <option value="">All categories</option>
        {availability?.categories.map((c) => (
          <option key={c} value={c}>
            {c.replace(/_/g, " ")}
          </option>
        ))}
      </select>

      <select
        value={filters.granularity}
        onChange={(e) => onChange({ ...filters, granularity: e.target.value as DashboardFilters["granularity"] })}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
      >
        <option value="day">Daily</option>
        <option value="week">Weekly</option>
        <option value="month">Monthly</option>
      </select>

      {(filters.start_date || filters.end_date || filters.category) && (
        <button
          type="button"
          onClick={() => onChange({ granularity: filters.granularity })}
          className="text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          Clear filters
        </button>
      )}

      {minDate && maxDate && (
        <span className="ml-auto text-xs text-slate-400">
          Data available {minDate} to {maxDate}
        </span>
      )}
    </div>
  );
}
