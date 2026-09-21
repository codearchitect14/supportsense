import { Database, MessagesSquare, PlugZap, TrendingUp } from "lucide-react";
import { Container } from "../ui/Container";
import { SectionHeading } from "../ui/SectionHeading";

const steps = [
  {
    icon: PlugZap,
    title: "Connect your data",
    description: "Import your support content and order history in minutes, no migration project required.",
  },
  {
    icon: Database,
    title: "We index your knowledge base",
    description: "Every article and past answer is embedded and stored for fast, accurate retrieval.",
  },
  {
    icon: MessagesSquare,
    title: "Customers chat, call, or ask",
    description: "The assistant answers from your content first, and reasons with an LLM only when it needs to.",
  },
  {
    icon: TrendingUp,
    title: "You watch it pay off",
    description: "Every conversation flows into the dashboard next to the revenue and orders it touched.",
  },
];

export function HowItWorks() {
  return (
    <section className="bg-white py-20 sm:py-28">
      <Container>
        <SectionHeading
          eyebrow="How it works"
          title="Live in an afternoon, not a quarter"
          description="No dedicated vector database to run, no per-seat AI platform fee. Just your data, connected."
        />

        <div className="relative mt-16 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div
            aria-hidden="true"
            className="absolute left-0 right-0 top-6 hidden h-px bg-slate-200 lg:block"
          />
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={step.title} className="relative text-center">
                <div className="relative mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-brand-200 bg-white text-brand-600 shadow-soft">
                  <Icon size={20} />
                  <span className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-brand-600 text-[11px] font-bold text-white">
                    {index + 1}
                  </span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.description}</p>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
