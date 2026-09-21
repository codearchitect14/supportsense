import { useEffect, useRef, type ReactNode } from "react";
import { MessageBubble } from "./MessageBubble";
import type { UiMessage } from "./types";

export function MessageList({
  messages,
  onFeedback,
  emptyState,
}: {
  messages: UiMessage[];
  onFeedback?: (messageId: string, helpful: boolean) => void;
  emptyState?: ReactNode;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return <div className="flex flex-1 items-center justify-center">{emptyState}</div>;
  }

  return (
    <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onFeedback={
            message.role === "assistant" && onFeedback && !message.streaming
              ? (helpful) => onFeedback(message.id, helpful)
              : undefined
          }
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
