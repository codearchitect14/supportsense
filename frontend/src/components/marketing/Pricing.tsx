import { Check } from "lucide-react";
import { Container } from "../ui/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { Card } from "../ui/Card";
import { ButtonLink } from "../ui/ButtonLink";
import { cn } from "../../lib/cn";

const tiers = [
  {
    name: "Starter",
    price: "$0",
    period: "/month",
    description: "For small teams validating the assistant on a single channel.",
    features: ["Up to 500 conversations/mo", "Chat assistant", "Community support"],
    cta: "Start free",
    highlighted: false,
  },
  {
    name: "Growth",
    price: "$149",
    period: "/month",
    description: "For support teams ready to add voice and full analytics.",
    features: [
      "Up to 10,000 conversations/mo",
      "Chat + voice assistant",
      "Revenue & analytics dashboard",
      "Priority email support",
    ],
    cta: "Request a demo",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For multi-brand or high-volume operations with custom needs.",
    features: [
      "Unlimited conversations",
      "Dedicated onboarding",
      "Custom role & access policies",
      "SLA-backed support",
    ],
    cta: "Talk to sales",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="bg-white py-20 sm:py-28">
      <Container>
        <SectionHeading
          eyebrow="Pricing"
          title="Illustrative plans that scale with conversation volume"
          description="Every plan runs on the same zero-markup free-tier LLM routing, so cost scales with usage, not seats."
        />

        <div className="mt-16 grid gap-6 lg:grid-cols-3">
          {tiers.map((tier) => (
            <Card
              key={tier.name}
              className={cn(
                "flex flex-col",
                tier.highlighted && "border-brand-300 ring-2 ring-brand-500",
              )}
            >
              {tier.highlighted && (
                <span className="mb-4 inline-flex w-fit items-center rounded-full bg-brand-600 px-3 py-1 text-xs font-semibold text-white">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-semibold text-slate-900">{tier.name}</h3>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-3xl font-bold text-slate-900">{tier.price}</span>
                <span className="text-sm text-slate-500">{tier.period}</span>
              </div>
              <p className="mt-3 text-sm text-slate-600">{tier.description}</p>

              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm text-slate-700">
                    <Check size={16} className="mt-0.5 shrink-0 text-accent-600" />
                    {feature}
                  </li>
                ))}
              </ul>

              <ButtonLink
                to="/login"
                variant={tier.highlighted ? "primary" : "secondary"}
                className="mt-8 justify-center"
              >
                {tier.cta}
              </ButtonLink>
            </Card>
          ))}
        </div>
      </Container>
    </section>
  );
}
