import { BarChart3, Mic, MessageSquareText } from "lucide-react";
import type { ReactNode } from "react";
import { Container } from "../ui/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { cn } from "../../lib/cn";

const features = [
  {
    id: "chat",
    icon: MessageSquareText,
    eyebrow: "AI chatbot & knowledge base",
    title: "Answers grounded in your actual support content",
    description:
      "Every response is retrieved from your real knowledge base before an LLM ever runs, with a semantic cache and automatic provider fallback keeping the assistant fast, accurate, and always available.",
    bullets: [
      "Retrieval-augmented answers, not model guesses",
      "Groq and Gemini fallback keeps uptime high",
      "Token usage tracked on every conversation",
    ],
    visual: (
      <div className="space-y-2.5">
        <div className="ml-auto w-3/4 rounded-xl rounded-tr-sm bg-brand-600 px-3 py-2 text-xs text-white">
          Can I get a refund on a damaged item?
        </div>
        <div className="w-4/5 rounded-xl rounded-tl-sm bg-white px-3 py-2 text-xs text-slate-700 shadow-sm">
          Yes, damaged items qualify for a full refund within 30 days. I can start that now.
        </div>
      </div>
    ),
  },
  {
    id: "voice",
    icon: Mic,
    eyebrow: "Voice agent",
    title: "The same assistant, now on the phone",
    description:
      "Speech is transcribed locally and handed to the same retrieval and reasoning pipeline as chat, so voice customers get identical accuracy, then hear a natural synthesized reply in seconds.",
    bullets: [
      "Local, on-device transcription",
      "Shares one knowledge base with chat",
      "Streamed audio replies, low latency",
    ],
    visual: (
      <div className="flex items-center justify-center gap-1.5">
        {[8, 20, 14, 28, 10, 24, 16, 30, 12].map((h, i) => (
          <span
            key={i}
            className="w-1.5 rounded-full bg-gradient-to-t from-brand-500 to-accent-400"
            style={{ height: `${h}px` }}
          />
        ))}
      </div>
    ),
  },
  {
    id: "analytics",
    icon: BarChart3,
    eyebrow: "Revenue & analytics dashboard",
    title: "Support performance, next to the revenue it protects",
    description:
      "Real order, payment, and review data sits alongside conversation volume and resolution rate, so leadership sees exactly what the assistant is doing for the business, not just for support.",
    bullets: [
      "Revenue, orders, and AOV trends",
      "Support metrics: volume, latency, provider mix",
      "CSV export on every chart and table",
    ],
    visual: (
      <div className="grid grid-cols-3 gap-2">
        {["Revenue", "Orders", "Resolved"].map((label, i) => (
          <div key={label} className="rounded-lg bg-white px-2.5 py-2 text-center shadow-sm">
            <p className="text-sm font-bold text-slate-900">
              {["$18.4k", "1,204", "94%"][i]}
            </p>
            <p className="text-[10px] text-slate-500">{label}</p>
          </div>
        ))}
      </div>
    ),
  },
];

export function Features() {
  return (
    <section id="product" className="py-20 sm:py-28">
      <Container>
        <SectionHeading
          eyebrow="Platform"
          title="One assistant, three ways to reach your customers"
          description="Chat, voice, and analytics all run on the same retrieval-augmented core, so accuracy and reporting never drift apart."
        />

        <div className="mt-16 space-y-16">
          {features.map((feature, index) => (
            <FeatureRow key={feature.id} feature={feature} reverse={index % 2 === 1} />
          ))}
        </div>
      </Container>
    </section>
  );
}

function FeatureRow({
  feature,
  reverse,
}: {
  feature: (typeof features)[number];
  reverse: boolean;
}) {
  const Icon = feature.icon;
  return (
    <div
      id={feature.id === "voice" ? "solutions" : undefined}
      className={cn(
        "grid items-center gap-10 lg:grid-cols-2",
        reverse && "lg:[&>*:first-child]:order-2",
      )}
    >
      <div>
        <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
          <Icon size={22} />
        </div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-brand-600">
          {feature.eyebrow}
        </p>
        <h3 className="text-2xl font-bold text-slate-900">{feature.title}</h3>
        <p className="mt-3 text-base leading-relaxed text-slate-600">{feature.description}</p>
        <ul className="mt-5 space-y-2.5">
          {feature.bullets.map((bullet) => (
            <BulletItem key={bullet}>{bullet}</BulletItem>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 shadow-card">
        {feature.visual}
      </div>
    </div>
  );
}

function BulletItem({ children }: { children: ReactNode }) {
  return (
    <li className="flex items-start gap-2.5 text-sm text-slate-700">
      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-500" />
      {children}
    </li>
  );
}
