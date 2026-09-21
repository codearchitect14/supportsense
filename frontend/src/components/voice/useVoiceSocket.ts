import { useCallback, useEffect, useRef, useState } from "react";
import { api, getAccessToken, WS_BASE_URL } from "../../lib/api";
import type { MessageOut } from "../../lib/types";
import type { UiMessage } from "../chat/types";

type RecordingState = "idle" | "recording" | "processing";

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

function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? "";
}

export function useVoiceSocket(initialConversationId?: string) {
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<ArrayBuffer[]>([]);
  const streamingIdRef = useRef<string | null>(null);

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
    const ws = new WebSocket(`${WS_BASE_URL}/voice/stream?token=${encodeURIComponent(token)}`);
    ws.binaryType = "arraybuffer";

    ws.onclose = () => {
      if (socketRef.current === ws) socketRef.current = null;
    };
    ws.onerror = () => setError("Lost connection to the voice assistant.");

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        audioChunksRef.current.push(event.data);
        return;
      }

      const data = JSON.parse(event.data);

      if (data.type === "transcript") {
        if (data.final) {
          setLiveTranscript("");
          if (data.text) {
            setMessages((prev) => [
              ...prev,
              { id: crypto.randomUUID(), role: "user", content: data.text },
            ]);
          }
        } else {
          setLiveTranscript(data.text ?? "");
        }
      } else if (data.type === "answer_delta") {
        if (!streamingIdRef.current) {
          const newId = crypto.randomUUID();
          streamingIdRef.current = newId;
          setMessages((prev) => [
            ...prev,
            { id: newId, role: "assistant", content: "", streaming: true },
          ]);
        }
        const id = streamingIdRef.current;
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

        if (audioChunksRef.current.length > 0) {
          const blob = new Blob(audioChunksRef.current, { type: "audio/mpeg" });
          audioChunksRef.current = [];
          setAudioUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev);
            return URL.createObjectURL(blob);
          });
        }
        setRecordingState("idle");
      } else if (data.type === "error") {
        streamingIdRef.current = null;
        setError(data.message ?? "The voice assistant could not respond.");
        setRecordingState("idle");
        setMessages((prev) => prev.filter((m) => !(m.streaming && m.content === "")));
      }
    };

    socketRef.current = ws;
    return ws;
  }, []);

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    setLiveTranscript("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ws = connect();
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;

      recorder.ondataavailable = async (event) => {
        if (event.data.size === 0) return;
        const buffer = await event.data.arrayBuffer();
        if (ws.readyState === WebSocket.OPEN) ws.send(buffer);
      };

      const openIfNeeded = new Promise<void>((resolve) => {
        if (ws.readyState === WebSocket.OPEN) resolve();
        else ws.addEventListener("open", () => resolve(), { once: true });
      });
      await openIfNeeded;

      recorder.start(500);
      setRecordingState("recording");
    } catch {
      setError("Microphone access was denied or is unavailable.");
      stopTracks();
    }
  }, [connect, stopTracks]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    stopTracks();
    setRecordingState("processing");

    const ws = socketRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ event: "end_utterance" }));
    }
  }, [stopTracks]);

  useEffect(() => {
    return () => {
      stopTracks();
      socketRef.current?.close();
      socketRef.current = null;
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendFeedback = useCallback(async (messageId: string, helpful: boolean) => {
    setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, feedback: helpful } : m)));
    try {
      await api.post(`/chat/messages/${messageId}/feedback`, { helpful });
    } catch {
      // Optimistic UI already reflects the click.
    }
  }, []);

  return {
    messages,
    conversationId,
    recordingState,
    liveTranscript,
    audioUrl,
    error,
    startRecording,
    stopRecording,
    sendFeedback,
  };
}
