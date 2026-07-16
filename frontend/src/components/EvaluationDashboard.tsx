import { useState } from "react";
import { api, type EvalReport } from "../api";
import { IconCheck } from "./icons";

function Mark({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="inline-grid h-5 w-5 place-items-center rounded-full bg-emerald-100 text-emerald-700">
      <IconCheck size={12} />
    </span>
  ) : (
    <span className="inline-grid h-5 w-5 place-items-center rounded-full bg-slate-100 text-slate-400">
      <span className="h-0.5 w-2 rounded bg-slate-400" />
    </span>
  );
}

export function EvaluationDashboard() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setReport(await api.runEval());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Evaluation Dashboard</h2>
        <button className="btn-primary" onClick={run} disabled={loading}>
          {loading ? "Running…" : "Run benchmark"}
        </button>
      </div>

      {error && <p className="text-xs text-rose-600">{error}</p>}
      {!report && !loading && (
        <p className="text-sm text-slate-400">
          Run the benchmark to compare the memory agent against a no-memory
          baseline across 24 diagnostic scenarios. Results are generated live
          for the currently configured model and strict keyword evaluator.
        </p>
      )}

      {report && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-3">
            <Metric label="Memory agent accuracy" value={pct(report.memory_agent_accuracy)} good />
            <Metric label="Baseline (no memory)" value={pct(report.baseline_no_memory_accuracy)} />
            <Metric label={`Recall in context (top ${report.retrieval_top_k})`} value={pct(report.memory_recall_at_context)} good />
            <Metric label="Token savings" value={`${report.token_savings_percent}%`} good />
            <Metric label="Outdated mem errors" value={`${report.outdated_memory_errors}`} good={report.outdated_memory_errors === 0} />
            <Metric label="Avg retrieval" value={`${report.avg_retrieval_latency_ms} ms`} />
          </div>

          <ComparisonBar
            agent={report.memory_agent_accuracy}
            baseline={report.baseline_no_memory_accuracy}
          />

          <table className="mt-4 w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase text-slate-400">
                <th className="py-1">Scenario</th>
                <th>Agent</th>
                <th>Baseline</th>
                <th>Tokens</th>
                <th>Leak</th>
              </tr>
            </thead>
            <tbody>
              {report.scenarios.map((s) => (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="py-1.5 text-slate-700">{s.title}</td>
                  <td><Mark ok={s.memory_agent_correct} /></td>
                  <td><Mark ok={s.baseline_correct} /></td>
                  <td className="text-slate-500">{s.tokens_used}</td>
                  <td>
                    {s.forbidden_leaked ? (
                      <span className="text-xs font-medium text-rose-600">leak</span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

const pct = (v: number) => `${Math.round(v * 100)}%`;

function Metric({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white/60 p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-xl font-semibold ${good ? "text-emerald-600" : "text-slate-700"}`}>
        {value}
      </div>
    </div>
  );
}

function ComparisonBar({ agent, baseline }: { agent: number; baseline: number }) {
  return (
    <div className="space-y-2">
      <Row label="Memory agent" value={agent} color="bg-brand-500" />
      <Row label="No-memory baseline" value={baseline} color="bg-slate-400" />
    </div>
  );
}

function Row({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="mb-0.5 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>{pct(value)}</span>
      </div>
      <div className="h-3 w-full rounded-full bg-slate-200">
        <div className={`h-3 rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}
