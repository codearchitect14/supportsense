import { useState } from "react";
import { FiltersBar } from "../../components/dashboard/FiltersBar";
import { OverviewSection } from "../../components/dashboard/sections/OverviewSection";
import { CustomersSection } from "../../components/dashboard/sections/CustomersSection";
import { OperationsSection } from "../../components/dashboard/sections/OperationsSection";
import { SupportSection } from "../../components/dashboard/sections/SupportSection";
import { cn } from "../../lib/cn";
import type { DashboardFilters } from "../../lib/analyticsTypes";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "customers", label: "Customers" },
  { id: "operations", label: "Operations" },
  { id: "support", label: "Support" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [filters, setFilters] = useState<DashboardFilters>({ granularity: "month" });

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">Dashboard</h1>
        <nav className="flex gap-1 rounded-lg bg-slate-100 p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors",
                activeTab === tab.id ? "bg-white text-brand-700 shadow-sm" : "text-slate-600 hover:text-slate-900",
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <FiltersBar filters={filters} onChange={setFilters} />

      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "overview" && <OverviewSection filters={filters} />}
        {activeTab === "customers" && <CustomersSection filters={filters} />}
        {activeTab === "operations" && <OperationsSection filters={filters} />}
        {activeTab === "support" && <SupportSection filters={filters} />}
      </div>
    </div>
  );
}
