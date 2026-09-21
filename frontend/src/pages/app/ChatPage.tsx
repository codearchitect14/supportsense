import { MessageSquareText } from "lucide-react";
import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChatComposer } from "../../components/chat/ChatComposer";
import { MessageList } from "../../components/chat/MessageList";
import { useChatSocket } from "../../components/chat/useChatSocket";
import { ErrorBanner } from "../../components/ui/ErrorBanner";

export function ChatPage() {
  const { conversationId: routeConversationId } = useParams();
  const navigate = useNavigate();
  const { messages, error, conversationId, sendMessage, sendFeedback } =
    useChatSocket(routeConversationId);

  const hasNavigatedRef = useRef(false);
  useEffect(() => {
    if (conversationId && conversationId !== routeConversationId && !hasNavigatedRef.current) {
      hasNavigatedRef.current = true;
      navigate(`/app/chat/${conversationId}`, { replace: true });
    }
  }, [conversationId, routeConversationId, navigate]);

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">Chat</h1>
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
            <MessageSquareText className="mx-auto mb-3 text-slate-300" size={36} />
            <p className="text-sm text-slate-500">
              Ask a question to start a conversation with the assistant.
            </p>
          </div>
        }
      />

      <ChatComposer onSend={sendMessage} />
    </div>
  );
}
