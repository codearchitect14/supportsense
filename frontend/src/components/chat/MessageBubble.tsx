import { ThumbsDown, ThumbsUp } from "lucide-react";
import { cn } from "../../lib/cn";
import { ProviderBadge } from "./ProviderBadge";
import { TypingIndicator } from "./TypingIndicator";
import type { UiMessage } from "./types";

export function MessageBubble({
  message,
  onFeedback,
}: {
  message: UiMessage;
  onFeedback?: (helpful: boolean) => void;
}) {
  const isUser = message.role === "user";
  const isEmptyStreaming = message.streaming && message.content.length === 0;

  return (
    <div className={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
      {isEmptyStreaming ? (
        <TypingIndicator />
      ) : (
        <div
          className={cn(
            "max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-brand-600 text-white"
              : "rounded-tl-sm bg-slate-100 text-slate-800",
          )}
        >
          {message.content}
          {message.streaming && (
            <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-current align-middle" />
          )}
        </div>
      )}

      {!isUser && !message.streaming && message.providerUsed && (
        <div className="mt-1.5 flex items-center gap-2">
          <ProviderBadge provider={message.providerUsed} tokens={message.tokensUsed} />

          {onFeedback && (
            <div className="flex items-center gap-0.5">
              <button
                type="button"
                aria-label="Mark as helpful"
                onClick={() => onFeedback(true)}
                className={cn(
                  "rounded-md p-1 hover:bg-slate-100",
                  message.feedback === true ? "text-accent-600" : "text-slate-400",
                )}
              >
                <ThumbsUp size={14} />
              </button>
              <button
                type="button"
                aria-label="Mark as not helpful"
                onClick={() => onFeedback(false)}
                className={cn(
                  "rounded-md p-1 hover:bg-slate-100",
                  message.feedback === false ? "text-red-500" : "text-slate-400",
                )}
              >
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
