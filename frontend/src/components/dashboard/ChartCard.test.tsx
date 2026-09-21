import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChartCard } from "./ChartCard";

describe("ChartCard", () => {
  it("renders children when not loading or empty", () => {
    render(
      <ChartCard title="Revenue over time">
        <div>chart contents</div>
      </ChartCard>,
    );
    expect(screen.getByText("Revenue over time")).toBeInTheDocument();
    expect(screen.getByText("chart contents")).toBeInTheDocument();
  });

  it("shows a skeleton instead of children while loading", () => {
    render(
      <ChartCard title="Revenue over time" loading>
        <div>chart contents</div>
      </ChartCard>,
    );
    expect(screen.queryByText("chart contents")).not.toBeInTheDocument();
  });

  it("shows an empty-state message instead of children when empty", () => {
    render(
      <ChartCard title="Revenue over time" empty>
        <div>chart contents</div>
      </ChartCard>,
    );
    expect(screen.queryByText("chart contents")).not.toBeInTheDocument();
    expect(screen.getByText(/no data for this filter/i)).toBeInTheDocument();
  });

  it("shows a CSV export link only when not loading and not empty", () => {
    const { rerender } = render(
      <ChartCard title="Revenue over time" exportHref="/export.csv">
        <div>chart contents</div>
      </ChartCard>,
    );
    expect(screen.getByText("CSV")).toBeInTheDocument();

    rerender(
      <ChartCard title="Revenue over time" exportHref="/export.csv" loading>
        <div>chart contents</div>
      </ChartCard>,
    );
    expect(screen.queryByText("CSV")).not.toBeInTheDocument();
  });
});
