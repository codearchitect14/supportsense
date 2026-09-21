import { Container } from "../ui/Container";
import { Card } from "../ui/Card";
import { Quote } from "lucide-react";

const testimonials = [
  {
    quote:
      "We stopped dreading the LLM bill. Most questions never reach the model at all, and the ones that do get answered from our own docs, not a guess.",
    name: "Jordan Ellis",
    title: "Head of Customer Experience, Northpeak",
  },
  {
    quote:
      "The dashboard is the first time support and finance have looked at the same numbers. Escalation rate next to order volume changed how we staff.",
    name: "Priya Nathan",
    title: "VP Operations, Vertex Retail",
  },
  {
    quote:
      "Voice was the surprise. Customers get the same accurate answer whether they type or call, and setup took an afternoon, not a sprint.",
    name: "Marcus Ade",
    title: "Director of Support, Solstice Goods",
  },
];

export function Testimonials() {
  return (
    <section className="py-20 sm:py-28">
      <Container>
        <p className="mb-4 text-center text-sm font-semibold uppercase tracking-wider text-brand-600">
          What teams say
        </p>
        <h2 className="mx-auto max-w-xl text-center text-3xl font-bold text-slate-900 sm:text-4xl">
          Illustrative feedback from product testing
        </h2>

        <div className="mt-14 grid gap-6 lg:grid-cols-3">
          {testimonials.map((t) => (
            <Card key={t.name} className="flex flex-col">
              <Quote className="mb-4 text-brand-300" size={26} />
              <p className="flex-1 text-[15px] leading-relaxed text-slate-700">"{t.quote}"</p>
              <div className="mt-6 flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                  {t.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                  <p className="text-xs text-slate-500">{t.title}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Container>
    </section>
  );
}
