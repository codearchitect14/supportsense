import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MessageBubble } from "./MessageBubble";
import type { UiMessage } from "./types";

const baseMessage: UiMessage = {
  id: "1",
  role: "assistant",
  content: "Refunds are processed within 5 business days.",
  providerUsed: "groq",
  tokensUsed: 42,
};

describe("MessageBubble", () => {
  it("renders assistant content and provider badge", () => {
    render(<MessageBubble message={baseMessage} />);
    expect(screen.getByText(/refunds are processed/i)).toBeInTheDocument();
    expect(screen.getByText("Groq")).toBeInTheDocument();
    expect(screen.getByText(/42 tokens/)).toBeInTheDocument();
  });

  it("shows a typing indicator instead of content while streaming with no text yet", () => {
    render(<MessageBubble message={{ ...baseMessage, content: "", streaming: true }} />);
    expect(screen.queryByText(/refunds are processed/i)).not.toBeInTheDocument();
  });

  it("does not show the provider badge while still streaming", () => {
    render(<MessageBubble message={{ ...baseMessage, streaming: true }} />);
    expect(screen.queryByText("Groq")).not.toBeInTheDocument();
  });

  it("invokes onFeedback with the correct value for each button", () => {
    const onFeedback = vi.fn();
    render(<MessageBubble message={baseMessage} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Mark as helpful"));
    expect(onFeedback).toHaveBeenCalledWith(true);

    fireEvent.click(screen.getByLabelText("Mark as not helpful"));
    expect(onFeedback).toHaveBeenCalledWith(false);
  });

  it("omits feedback buttons for user messages", () => {
    const onFeedback = vi.fn();
    render(<MessageBubble message={{ ...baseMessage, role: "user", providerUsed: null }} onFeedback={onFeedback} />);
    expect(screen.queryByLabelText("Mark as helpful")).not.toBeInTheDocument();
  });
});
