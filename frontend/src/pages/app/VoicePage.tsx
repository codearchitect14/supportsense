import { Mic, Square } from "lucide-react";
import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { MessageList } from "../../components/chat/MessageList";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { cn } from "../../lib/cn";
import { useVoiceSocket } from "../../components/voice/useVoiceSocket";

export function VoicePage() {
  const { conversationId: routeConversationId } = useParams();
  const navigate = useNavigate();
  const {
    messages,
    conversationId,
    recordingState,
    liveTranscript,
    audioUrl,
    error,
    startRecording,
    stopRecording,
    sendFeedback,
  } = useVoiceSocket(routeConversationId);

  const hasNavigatedRef = useRef(false);
  useEffect(() => {
    if (conversationId && conversationId !== routeConversationId && !hasNavigatedRef.current) {
      hasNavigatedRef.current = true;
      navigate(`/app/voice/${conversationId}`, { replace: true });
    }
  }, [conversationId, routeConversationId, navigate]);

  const isRecording = recordingState === "recording";
  const isProcessing = recordingState === "processing";

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">Voice Agent</h1>
      </header>

      {error && (
        <div className="px-6 pt-4">
          <ErrorBanner message={error} />
        </div>
      )}

      <MessageList
        messages={messages}
        onFeedback={sendFeedback}
        emptyState={
          <div className="text-center">
            <Mic className="mx-auto mb-3 text-slate-300" size={36} />
            <p className="text-sm text-slate-500">Press the microphone and ask your question.</p>
          </div>
        }
      />

      {liveTranscript && (
        <div className="border-t border-slate-100 bg-slate-50 px-6 py-2">
          <p className="text-sm italic text-slate-500">{liveTranscript}</p>
        </div>
      )}

      <div className="flex flex-col items-center gap-3 border-t border-slate-200 bg-white p-6">
        {audioUrl && (
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <audio src={audioUrl} controls autoPlay className="h-9 w-full max-w-sm" />
        )}

        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={cn(
            "flex h-16 w-16 items-center justify-center rounded-full text-white shadow-soft transition-colors",
            isRecording ? "animate-pulse bg-red-500 hover:bg-red-600" : "bg-brand-600 hover:bg-brand-700",
            isProcessing && "cursor-not-allowed opacity-60",
          )}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
        >
          {isRecording ? <Square size={22} /> : <Mic size={24} />}
        </button>

        <p className="text-xs font-medium text-slate-500">
          {isRecording ? "Listening… tap to stop" : isProcessing ? "Thinking…" : "Tap to speak"}
        </p>
      </div>
    </div>
  );
}
