import { ArrowRight, Sparkles } from "lucide-react";
import { Container } from "../ui/Container";
import { ButtonLink } from "../ui/ButtonLink";
import { ProductMockup } from "./ProductMockup";

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden pt-16 pb-20 sm:pt-24 sm:pb-28">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 flex justify-center blur-3xl"
      >
        <div className="h-[420px] w-[820px] rounded-full bg-gradient-to-tr from-brand-200 via-brand-100 to-accent-400/30 opacity-60" />
      </div>

      <Container className="grid items-center gap-16 lg:grid-cols-2">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1.5 text-sm font-medium text-brand-700">
            <Sparkles size={15} />
            Now with automatic multi-provider AI fallback
          </div>

          <h1 className="text-4xl font-bold leading-[1.1] text-slate-900 sm:text-5xl lg:text-[3.25rem]">
            AI customer support that knows your business,{" "}
            <span className="bg-gradient-to-r from-brand-600 to-accent-600 bg-clip-text text-transparent">
              backed by real revenue intelligence
            </span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
            SupportSense pairs a retrieval-grounded chat and voice assistant with a live
            analytics dashboard, so every conversation is accurate and every resolution shows
            up in the numbers leadership actually looks at.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <ButtonLink to="/login" size="lg" className="group">
              Request a demo
              <ArrowRight size={18} className="transition-transform group-hover:translate-x-0.5" />
            </ButtonLink>
            <ButtonLink to="/login" size="lg" variant="secondary">
              Start free
            </ButtonLink>
          </div>

          <p className="mt-5 text-sm text-slate-500">
            No credit card required &middot; Free tier available &middot; Set up in minutes
          </p>
        </div>

        <ProductMockup />
      </Container>
    </section>
  );
}
