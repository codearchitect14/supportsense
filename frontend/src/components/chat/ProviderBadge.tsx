import { cn } from "../../lib/cn";

const labels: Record<string, string> = {
  groq: "Groq",
  gemini: "Gemini",
  kb_direct: "Knowledge base",
  cache: "Cached answer",
};

const styles: Record<string, string> = {
  groq: "bg-orange-50 text-orange-700 ring-orange-500/20",
  gemini: "bg-blue-50 text-blue-700 ring-blue-500/20",
  kb_direct: "bg-accent-500/10 text-accent-600 ring-accent-500/20",
  cache: "bg-brand-50 text-brand-700 ring-brand-500/20",
};

export function ProviderBadge({ provider, tokens }: { provider: string; tokens?: number | null }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1",
        styles[provider] ?? "bg-slate-100 text-slate-600 ring-slate-300",
      )}
    >
      {labels[provider] ?? provider}
      {typeof tokens === "number" && tokens > 0 && <span className="opacity-70">· {tokens} tokens</span>}
    </span>
  );
}
