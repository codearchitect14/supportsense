import { Navbar } from "../components/marketing/Navbar";
import { Hero } from "../components/marketing/Hero";
import { LogoStrip } from "../components/marketing/LogoStrip";
import { Features } from "../components/marketing/Features";
import { HowItWorks } from "../components/marketing/HowItWorks";
import { Metrics } from "../components/marketing/Metrics";
import { Testimonials } from "../components/marketing/Testimonials";
import { Pricing } from "../components/marketing/Pricing";
import { FAQ } from "../components/marketing/FAQ";
import { Footer } from "../components/marketing/Footer";

export function MarketingHome() {
  return (
    <div className="min-h-screen bg-[#fafafa]">
      <Navbar />
      <main>
        <Hero />
        <LogoStrip />
        <Features />
        <HowItWorks />
        <Metrics />
        <Testimonials />
        <Pricing />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}
