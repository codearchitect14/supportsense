import { type FormEvent, useState } from "react";
import { Container } from "../ui/Container";
import { Logo } from "../ui/Logo";
import { Button } from "../ui/Button";

const columns = [
  {
    title: "Product",
    links: ["Chat assistant", "Voice agent", "Analytics dashboard", "Pricing"],
  },
  {
    title: "Company",
    links: ["About", "Careers", "Blog", "Contact"],
  },
  {
    title: "Legal",
    links: ["Privacy policy", "Terms of service", "Security"],
  },
];

export function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!email) return;
    setSubscribed(true);
    setEmail("");
  }

  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <Container className="py-16">
        <div className="grid gap-12 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-slate-600">
              AI customer support, voice, and revenue intelligence for e-commerce and retail
              teams.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 max-w-sm">
              <label htmlFor="newsletter-email" className="text-sm font-medium text-slate-700">
                Get product updates
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  id="newsletter-email"
                  type="email"
                  required
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
                <Button type="submit" size="md" className="shrink-0">
                  Subscribe
                </Button>
              </div>
              {subscribed && (
                <p className="mt-2 text-sm font-medium text-accent-600">
                  You&apos;re on the list, thanks!
                </p>
              )}
            </form>
          </div>

          {columns.map((column) => (
            <div key={column.title}>
              <h4 className="text-sm font-semibold text-slate-900">{column.title}</h4>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link}>
                    <a href="#top" className="text-sm text-slate-600 hover:text-brand-700">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-slate-200 pt-8 sm:flex-row">
          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} SupportSense. All rights reserved.
          </p>
          <p className="text-xs text-slate-400">
            Illustrative product site built for demonstration purposes.
          </p>
        </div>
      </Container>
    </footer>
  );
}
