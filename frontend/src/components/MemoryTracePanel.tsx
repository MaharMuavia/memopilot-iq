import type { ChatResponse, ScoredMemory } from "../api";

export function MemoryTracePanel({ last }: { last: ChatResponse | null }) {
  if (!last) {
    return (
      <div className="glass p-4 text-sm text-slate-500">
        Send a chat message to see the Memory Trace — exactly which memories
        were retrieved, scored, injected, or skipped, and why.
      </div>
    );
  }
  const { trace } = last;
  const pct = trace.token_budget
    ? Math.min(100, Math.round((trace.tokens_used / trace.token_budget) * 100))
    : 0;

  return (
    <div className="glass space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Memory Trace</h2>
        <span className="text-xs text-slate-400">
          {trace.retrieval_latency_ms.toFixed(1)} ms · {trace.candidates_considered} candidates
        </span>
      </div>

      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>Context budget</span>
          <span>
            {trace.tokens_used} / {trace.token_budget} tokens
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-200">
          <div
            className={`h-2 rounded-full ${pct > 90 ? "bg-rose-500" : "bg-brand-500"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <Section title={`Injected into context (${trace.included.length})`} items={trace.included} included />
      <Section title={`Skipped (${trace.skipped.length})`} items={trace.skipped} />

      {trace.notes.length > 0 && (
        <ul className="list-disc space-y-0.5 pl-5 text-xs text-slate-400">
          {trace.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Section({
  title,
  items,
  included,
}: {
  title: string;
  items: ScoredMemory[];
  included?: boolean;
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h3>
      <div className="space-y-2">
        {items.map((s) => (
          <div
            key={s.memory.memory_id}
            className={`rounded-xl border p-2.5 text-sm ${
              included ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200 bg-white/50"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-slate-700">{s.memory.content}</span>
              <span className="shrink-0 font-mono text-xs text-slate-500">
                {s.score.toFixed(2)}
              </span>
            </div>
            <div className="mt-1 text-[11px] text-slate-400">{s.reason}</div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {Object.entries(s.components)
                .filter(([, v]) => Math.abs(v) > 0.001)
                .map(([k, v]) => (
                  <span
                    key={k}
                    className={`chip ${v < 0 ? "bg-rose-50 text-rose-600" : "bg-slate-100 text-slate-500"}`}
                  >
                    {k.replace(/_/g, " ")}: {v.toFixed(2)}
                  </span>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
