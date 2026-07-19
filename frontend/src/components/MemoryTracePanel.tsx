import { useEffect, useState } from "react";
import type { ChatResponse, ScoredMemory } from "../api";

export function MemoryTracePanel({ last }: { last: ChatResponse | null }) {
  const [showRejected, setShowRejected] = useState(false);
  useEffect(() => setShowRejected(false), [last]);

  if (!last) {
    return (
      <div className="glass p-4 text-sm text-slate-500">
        Send a chat message to see the Memory Trace - exactly which memories were retrieved, scored, injected, or rejected, and why.
      </div>
    );
  }

  const { trace } = last;
  const pct = trace.token_budget ? Math.min(100, Math.round((trace.tokens_used / trace.token_budget) * 100)) : 0;
  const relevanceRejected = trace.skipped.filter((item) => item.reason.toLowerCase().includes("below relevance threshold"));
  const otherSkipped = trace.skipped.filter((item) => !item.reason.toLowerCase().includes("below relevance threshold"));

  return (
    <div className="glass space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Memory Trace</h2>
        <span className="text-xs text-slate-400">{trace.retrieval_latency_ms.toFixed(1)} ms / {trace.candidates_considered} scanned</span>
      </div>
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>Context budget</span>
          <span>{trace.tokens_used} / {trace.token_budget} tokens</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-200">
          <div className={`h-2 rounded-full ${pct > 90 ? "bg-rose-500" : "bg-brand-500"}`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      <Section title={`Injected into Qwen context (${trace.included.length})`} items={trace.included} included />
      <Section title={`Other skipped (${otherSkipped.length})`} items={otherSkipped} />

      {relevanceRejected.length > 0 && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Relevance gate protected the prompt</h3>
              <p className="mt-1 text-xs text-slate-600">
                {relevanceRejected.length} unrelated candidate{relevanceRejected.length === 1 ? " was" : "s were"} rejected before Qwen. No irrelevant memory entered the answer context.
              </p>
            </div>
            <button className="shrink-0 text-xs font-semibold text-emerald-700 underline-offset-2 hover:underline" onClick={() => setShowRejected((current) => !current)}>
              {showRejected ? "Hide details" : "Inspect"}
            </button>
          </div>
          {showRejected && <div className="mt-3"><Section title="Rejected candidates" items={relevanceRejected} /></div>}
        </div>
      )}

      {trace.notes.length > 0 && (
        <ul className="list-disc space-y-0.5 pl-5 text-xs text-slate-400">
          {trace.notes.map((note, index) => <li key={index}>{note}</li>)}
        </ul>
      )}
    </div>
  );
}

function Section({ title, items, included }: { title: string; items: ScoredMemory[]; included?: boolean }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</h3>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.memory.memory_id} className={`rounded-xl border p-2.5 text-sm ${included ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200 bg-white/50"}`}>
            <div className="flex items-start justify-between gap-2">
              <span className="text-slate-700">{item.memory.content}</span>
              <span className="shrink-0 font-mono text-xs text-slate-500">{item.score.toFixed(2)}</span>
            </div>
            <div className="mt-1 text-[11px] text-slate-400">{item.reason}</div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {Object.entries(item.components).filter(([, value]) => Math.abs(value) > 0.001).map(([key, value]) => (
                <span key={key} className={`chip ${value < 0 ? "bg-rose-50 text-rose-600" : "bg-slate-100 text-slate-500"}`}>
                  {key.replace(/_/g, " ")}: {value.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
