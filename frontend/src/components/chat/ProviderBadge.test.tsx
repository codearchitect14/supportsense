import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProviderBadge } from "./ProviderBadge";

describe("ProviderBadge", () => {
  it.each([
    ["groq", "Groq"],
    ["gemini", "Gemini"],
    ["kb_direct", "Knowledge base"],
    ["cache", "Cached answer"],
  ])("maps provider %s to label %s", (provider, label) => {
    render(<ProviderBadge provider={provider} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("falls back to the raw provider name for an unrecognized provider", () => {
    render(<ProviderBadge provider="mystery_llm" />);
    expect(screen.getByText("mystery_llm")).toBeInTheDocument();
  });

  it("shows token count only when tokens is a positive number", () => {
    const { rerender } = render(<ProviderBadge provider="groq" tokens={17} />);
    expect(screen.getByText(/17 tokens/)).toBeInTheDocument();

    rerender(<ProviderBadge provider="groq" tokens={0} />);
    expect(screen.queryByText(/tokens/)).not.toBeInTheDocument();

    rerender(<ProviderBadge provider="groq" tokens={null} />);
    expect(screen.queryByText(/tokens/)).not.toBeInTheDocument();
  });
});
