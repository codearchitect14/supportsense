import { useEffect, useState } from "react";
import { api } from "./api";
import type { DashboardFilters } from "./analyticsTypes";

function buildQuery(filters: DashboardFilters, extra?: Record<string, string | undefined>): string {
  const params = new URLSearchParams();
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.category) params.set("category", filters.category);
  params.set("granularity", filters.granularity);
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (value) params.set(key, value);
    }
  }
  return params.toString();
}

export function useAnalyticsQuery<T>(
  path: string,
  filters: DashboardFilters,
  extra?: Record<string, string | undefined>,
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .get<T>(`${path}?${buildQuery(filters, extra)}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load this data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, filters.start_date, filters.end_date, filters.category, filters.granularity, JSON.stringify(extra)]);

  return { data, loading, error };
}

export function analyticsQueryString(filters: DashboardFilters, extra?: Record<string, string | undefined>): string {
  return buildQuery(filters, extra);
}
