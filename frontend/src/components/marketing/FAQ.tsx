import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Container } from "../ui/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { cn } from "../../lib/cn";

const faqs = [
  {
    question: "Does the assistant ever answer from the model's own memory?",
    answer:
      "No. Every answer is grounded in your knowledge base first. The LLM is only called to compose a response from retrieved content, and only when a confident direct match isn't found.",
  },
  {
    question: "What happens if one AI provider is down or rate limited?",
    answer:
      "The provider router detects rate limits and automatically fails over to the secondary provider, then switches back once the primary's quota resets. Customers never see the difference.",
  },
  {
    question: "Can voice and chat share the same conversation history?",
    answer:
      "Yes. Voice transcripts are fed into the same chat orchestration engine, so retrieval, caching, and conversation memory all work identically across channels.",
  },
  {
    question: "How is my data secured?",
    answer:
      "Access is role-based with full audit logging on authentication and analytics access, all traffic is encrypted, and secrets are never stored in source control.",
  },
  {
    question: "Do I need my own vector database?",
    answer:
      "No. Retrieval runs on PostgreSQL with pgvector, so there's no separate vector infrastructure to provision or pay for.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="py-20 sm:py-28">
      <Container className="max-w-3xl">
        <SectionHeading eyebrow="FAQ" title="Questions, answered" />

        <div className="mt-12 divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white">
          {faqs.map((faq, index) => {
            const isOpen = openIndex === index;
            return (
              <div key={faq.question}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                  onClick={() => setOpenIndex(isOpen ? null : index)}
                  aria-expanded={isOpen}
                >
                  <span className="text-[15px] font-semibold text-slate-900">
                    {faq.question}
                  </span>
                  <ChevronDown
                    size={18}
                    className={cn(
                      "shrink-0 text-slate-400 transition-transform duration-200",
                      isOpen && "rotate-180 text-brand-600",
                    )}
                  />
                </button>
                {isOpen && (
                  <p className="px-6 pb-5 text-sm leading-relaxed text-slate-600">
                    {faq.answer}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
