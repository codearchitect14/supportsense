import { useCallback, useEffect, useRef, useState } from "react";
import { api, getAccessToken, WS_BASE_URL } from "../../lib/api";
import type { MessageOut } from "../../lib/types";
import type { UiMessage } from "./types";

function toUiMessage(m: MessageOut): UiMessage {
  return {
    id: m.id,
    role: m.role as "user" | "assistant",
    content: m.content,
    providerUsed: m.provider_used,
    tokensUsed: m.tokens_used,
    feedback: m.feedback,
  };
}

export function useChatSocket(initialConversationId?: string) {
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const streamingIdRef = useRef<string | null>(null);

  useEffect(() => {
    setConversationId(initialConversationId);
  }, [initialConversationId]);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    api
      .get<MessageOut[]>(`/conversations/${conversationId}/messages`)
      .then((history) => {
        if (!cancelled) setMessages(history.map(toUiMessage));
      })
      .catch(() => {
        if (!cancelled) setError("Could not load this conversation.");
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  const connect = useCallback((): WebSocket => {
    if (socketRef.current && socketRef.current.readyState <= WebSocket.OPEN) {
      return socketRef.current;
    }
    const token = getAccessToken() ?? "";
    const ws = new WebSocket(`${WS_BASE_URL}/chat/stream?token=${encodeURIComponent(token)}`);

    ws.onclose = () => {
      if (socketRef.current === ws) socketRef.current = null;
    };
    ws.onerror = () => setError("Lost connection to the assistant.");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "delta") {
        const id = streamingIdRef.current;
        if (!id) return;
        setMessages((prev) =>
          prev.map((m) => (m.id === id ? { ...m, content: m.content + data.text } : m)),
        );
      } else if (data.type === "done") {
        const id = streamingIdRef.current;
        streamingIdRef.current = null;
        setConversationId(data.conversation_id);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === id
              ? {
                  ...m,
                  id: data.message_id,
                  streaming: false,
                  providerUsed: data.provider_used,
                  tokensUsed: data.tokens_used,
                }
              : m,
          ),
        );
      } else if (data.type === "error") {
        streamingIdRef.current = null;
        setError(data.message ?? "The assistant could not respond.");
        setMessages((prev) => prev.filter((m) => !(m.streaming && m.content === "")));
      }
    };

    socketRef.current = ws;
    return ws;
  }, []);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, []);

  const sendMessage = useCallback(
    (text: string) => {
      setError(null);
      const ws = connect();

      const userMessage: UiMessage = { id: crypto.randomUUID(), role: "user", content: text };
      const assistantId = crypto.randomUUID();
      streamingIdRef.current = assistantId;
      setMessages((prev) => [
        ...prev,
        userMessage,
        { id: assistantId, role: "assistant", content: "", streaming: true },
      ]);

      const payload = JSON.stringify({ conversation_id: conversationId ?? null, message: text });
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(payload);
      } else {
        ws.addEventListener("open", () => ws.send(payload), { once: true });
      }
    },
    [connect, conversationId],
  );

  const sendFeedback = useCallback(async (messageId: string, helpful: boolean) => {
    setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, feedback: helpful } : m)));
    try {
      await api.post(`/chat/messages/${messageId}/feedback`, { helpful });
    } catch {
      // Optimistic UI already reflects the click; a failed write here isn't worth surfacing.
    }
  }, []);

  return { messages, error, conversationId, sendMessage, sendFeedback };
}
