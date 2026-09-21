import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatTile } from "./StatTile";

describe("StatTile", () => {
  it("renders the label and value", () => {
    render(<StatTile label="Total revenue" value="$12,450" />);
    expect(screen.getByText("Total revenue")).toBeInTheDocument();
    expect(screen.getByText("$12,450")).toBeInTheDocument();
  });

  it("shows a loading skeleton instead of the value", () => {
    render(<StatTile label="Total revenue" value="$12,450" loading />);
    expect(screen.queryByText("$12,450")).not.toBeInTheDocument();
  });

  it("labels an upward change with a plus sign", () => {
    render(<StatTile label="Orders" value="120" changePct={5.2} />);
    expect(screen.getByText("+5.2%")).toBeInTheDocument();
  });

  it("labels a downward change without a plus sign", () => {
    render(<StatTile label="Orders" value="120" changePct={-3.1} />);
    expect(screen.getByText("-3.1%")).toBeInTheDocument();
  });

  it("labels a near-zero change as flat", () => {
    render(<StatTile label="Orders" value="120" changePct={0.01} />);
    expect(screen.getByText("flat")).toBeInTheDocument();
  });

  it("omits the change badge when changePct is not provided", () => {
    render(<StatTile label="Orders" value="120" />);
    expect(screen.queryByText(/vs\. prior period/)).not.toBeInTheDocument();
  });
});
