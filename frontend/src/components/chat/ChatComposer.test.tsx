import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "./ChatComposer";

describe("ChatComposer", () => {
  it("sends trimmed text and clears the input", () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/ask about an order/i);
    fireEvent.change(textarea, { target: { value: "  how do I get a refund?  " } });
    fireEvent.click(screen.getByLabelText("Send message"));

    expect(onSend).toHaveBeenCalledWith("how do I get a refund?");
    expect(textarea).toHaveValue("");
  });

  it("submits on Enter without a shift key, and inserts a newline with shift", () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/ask about an order/i);
    fireEvent.change(textarea, { target: { value: "hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();

    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not send an empty or whitespace-only message", () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} />);

    fireEvent.click(screen.getByLabelText("Send message"));
    expect(onSend).not.toHaveBeenCalled();

    const textarea = screen.getByPlaceholderText(/ask about an order/i);
    fireEvent.change(textarea, { target: { value: "   " } });
    fireEvent.click(screen.getByLabelText("Send message"));
    expect(onSend).not.toHaveBeenCalled();
  });

  it("ignores submissions while disabled", () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} disabled />);

    const textarea = screen.getByPlaceholderText(/ask about an order/i);
    fireEvent.change(textarea, { target: { value: "hello" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    expect(onSend).not.toHaveBeenCalled();
  });
});
