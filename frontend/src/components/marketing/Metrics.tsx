import { Container } from "../ui/Container";

const metrics = [
  { value: "<1.2s", label: "Typical response time" },
  { value: "94%", label: "Resolved without escalation" },
  { value: "99.9%", label: "Assistant uptime target" },
  { value: "60%", label: "Fewer LLM calls via KB + cache" },
];

export function Metrics() {
  return (
    <section className="bg-brand-900 py-16">
      <Container>
        <p className="mb-10 text-center text-sm font-medium text-brand-200">
          Platform performance targets
        </p>
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="text-center">
              <p className="font-heading text-3xl font-bold text-white sm:text-4xl">
                {metric.value}
              </p>
              <p className="mt-2 text-sm text-brand-200">{metric.label}</p>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
