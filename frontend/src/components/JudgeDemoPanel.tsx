import { useState } from "react";
import { api, type DemoResult } from "../api";
import { IconPlay } from "./icons";

export function JudgeDemoPanel({ onComplete }: { onComplete?: () => void }) {
  const [result, setResult] = useState<DemoResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const r = await api.runDemo();
      setResult(r);
      setOpen(true);
      onComplete?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mb-5 overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-r from-brand-50 to-indigo-50 shadow-glass">
      <div className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand-600 text-white shadow-glass">
            <IconPlay size={16} />
          </span>
          <div>
            <h3 className="text-sm font-bold text-slate-800">
              Run the 90-second Judge Demo
            </h3>
            <p className="text-xs text-slate-500">
              Replays 4 sessions: memory creation → cross-session recall →
              supersession → critical recall, with full trace accounting.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <button className="btn-ghost py-2 text-sm" onClick={() => setOpen((o) => !o)}>
              {open ? "Hide" : "Show"} results
            </button>
          )}
          <button className="btn-primary px-4 py-2 text-sm" onClick={run} disabled={loading}>
            {loading ? "Running…" : "Run Judge Demo"}
          </button>
        </div>
      </div>

      {error && <p className="px-4 pb-3 text-xs text-rose-600">{error}</p>}

      {result && open && (
        <div className="stagger space-y-3 border-t border-brand-200/70 bg-white/70 p-4">
          {result.turns.map((t, i) => (
            <div key={t.session_id} className="rounded-xl border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="grid h-6 w-6 place-items-center rounded-full bg-brand-600 text-xs font-bold text-white">
                  {i + 1}
                </span>
                <span className="text-xs font-semibold text-slate-500">{t.session_id}</span>
                <span className="text-sm text-slate-700">“{t.message}”</span>
              </div>
              <p className="mt-1.5 text-[11px] italic text-slate-400">{t.expectation}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {t.actions.created > 0 && (
                  <span className="chip bg-emerald-100 text-emerald-700">
                    +{t.actions.created} created
                  </span>
                )}
                {t.actions.superseded > 0 && (
                  <span className="chip bg-rose-100 text-rose-700">
                    ↻ {t.actions.superseded} superseded
                  </span>
                )}
                {t.injected_memories.length > 0 && (
                  <span className="chip bg-brand-50 text-brand-700">
                    {t.injected_memories.length} memories recalled
                  </span>
                )}
                {t.injected_memories.some((m) => m.is_critical) && (
                  <span className="chip bg-red-100 text-red-700">critical pinned</span>
                )}
                <span className="chip bg-slate-100 text-slate-500">
                  {t.trace.tokens_used}/{t.trace.token_budget} tokens
                </span>
              </div>
            </div>
          ))}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3">
              <h4 className="text-xs font-semibold uppercase text-emerald-700">
                Active memory ({result.final_state.active.length})
              </h4>
              <ul className="mt-1 space-y-0.5 text-xs text-slate-600">
                {result.final_state.active.map((m, i) => (
                  <li key={i}>• {m}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-3">
              <h4 className="text-xs font-semibold uppercase text-rose-700">
                Superseded · ignored ({result.final_state.superseded.length})
              </h4>
              <ul className="mt-1 space-y-0.5 text-xs text-slate-500 line-through">
                {result.final_state.superseded.length === 0 && <li className="no-underline">—</li>}
                {result.final_state.superseded.map((m, i) => (
                  <li key={i}>• {m}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
