const bars = [38, 62, 45, 80, 56, 71, 90];

export function ProductMockup() {
  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="absolute -right-6 -top-6 -z-10 h-full w-full rounded-2xl bg-gradient-to-br from-accent-400/40 to-brand-400/30 blur-md"
      />
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
        {/* fake browser chrome */}
        <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50 px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
          <span className="ml-3 rounded-md bg-white px-3 py-1 text-xs text-slate-400 ring-1 ring-slate-200">
            app.supportsense.ai
          </span>
        </div>

        <div className="grid grid-cols-5">
          {/* chat panel */}
          <div className="col-span-3 border-r border-slate-100 p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Live conversation
            </p>

            <div className="space-y-3">
              <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-brand-600 px-3.5 py-2.5 text-sm text-white">
                Where is order #48213? It was supposed to arrive Tuesday.
              </div>
              <div className="max-w-[90%] rounded-2xl rounded-tl-sm bg-slate-100 px-3.5 py-2.5 text-sm text-slate-700">
                Your order shipped on the 12th and is on track for tomorrow. I&apos;ve sent the
                tracking link to your email.
                <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-accent-600 ring-1 ring-accent-500/30">
                  Answered from knowledge base &middot; 0 tokens
                </div>
              </div>
              <div className="ml-auto max-w-[70%] rounded-2xl rounded-tr-sm bg-brand-600 px-3.5 py-2.5 text-sm text-white">
                Perfect, thank you!
              </div>
            </div>
          </div>

          {/* mini dashboard panel */}
          <div className="col-span-2 p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Revenue today
            </p>
            <p className="text-2xl font-bold text-slate-900">$18,420</p>
            <p className="mb-4 text-xs font-medium text-accent-600">+12.4% vs. yesterday</p>

            <div className="flex h-20 items-end gap-1.5">
              {bars.map((height, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t-sm bg-gradient-to-t from-brand-500 to-accent-400"
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>

            <div className="mt-4 flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-xs">
              <span className="text-slate-500">Resolved without escalation</span>
              <span className="font-semibold text-slate-900">94%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
