import { History, Mic, MessageSquareText, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Input } from "../../components/ui/Input";
import { api } from "../../lib/api";
import { cn } from "../../lib/cn";
import type { Channel, ConversationSummary } from "../../lib/types";

type ChannelFilter = "all" | Channel;

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function HistoryPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [channel, setChannel] = useState<ChannelFilter>("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (channel !== "all") params.set("channel", channel);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (search.trim()) params.set("search", search.trim());

    const handle = setTimeout(() => {
      setLoading(true);
      api
        .get<ConversationSummary[]>(`/conversations?${params.toString()}`)
        .then(setConversations)
        .catch(() => setError("Could not load conversation history."))
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(handle);
  }, [channel, startDate, endDate, search]);

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">Conversation History</h1>
      </header>

      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-4">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <Input
            placeholder="Search conversation content…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex overflow-hidden rounded-lg border border-slate-300">
          {(["all", "chat", "voice"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setChannel(value)}
              className={cn(
                "px-3 py-2 text-sm font-medium capitalize transition-colors",
                channel === value ? "bg-brand-600 text-white" : "bg-white text-slate-600 hover:bg-slate-50",
              )}
            >
              {value}
            </button>
          ))}
        </div>

        <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-auto" />
        <span className="text-sm text-slate-400">to</span>
        <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-auto" />
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!error && !loading && conversations.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <History className="mx-auto mb-3 text-slate-300" size={36} />
              <p className="text-sm text-slate-500">No conversations match these filters.</p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {conversations.map((conversation) => (
            <Link
              key={conversation.id}
              to={`/app/${conversation.channel}/${conversation.id}`}
              className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3.5 transition-colors hover:border-brand-300 hover:bg-brand-50/40"
            >
              <div
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                  conversation.channel === "voice"
                    ? "bg-accent-500/10 text-accent-600"
                    : "bg-brand-50 text-brand-600",
                )}
              >
                {conversation.channel === "voice" ? <Mic size={16} /> : <MessageSquareText size={16} />}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-900">
                  {conversation.last_message_preview ?? "New conversation"}
                </p>
                <p className="text-xs text-slate-500">
                  {conversation.message_count} message{conversation.message_count === 1 ? "" : "s"} ·{" "}
                  {formatDate(conversation.last_message_at ?? conversation.started_at)}
                </p>
              </div>

              <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                {conversation.channel}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
