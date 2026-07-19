import { useEffect, useState } from "react";
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

  useEffect(() => {
    void api.getEvalReport().then(setReport).catch(() => {
      // No report exists until an administrator completes the first run.
    });
  }, []);

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

  function downloadReport() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `memopilot-eval-${report.generated_at.slice(0, 10)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="glass p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-700">Evaluation Dashboard</h2>
          {report && (
            <p className="mt-0.5 text-xs text-slate-400">
              {report.primary_backbone} · {report.evaluator} · {report.duration_seconds}s
              {` · build ${report.build_sha.slice(0, 12)}`}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {report && (
            <button className="btn-ghost" onClick={downloadReport}>
              Download JSON
            </button>
          )}
          <button className="btn-primary" onClick={run} disabled={loading}>
            {loading ? "Running…" : "Run benchmark (admin)"}
          </button>
        </div>
      </div>

      {error && <p className="text-xs text-rose-600">{error}</p>}
      {!report && !loading && (
        <p className="text-sm text-slate-400">
          Compare governed memory against no-memory, raw full-history, and
          model-generated history-summary baselines across 24 scenarios.
          Results are generated live for the configured model.
        </p>
      )}

      {report && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label="Memory agent accuracy" value={pct(report.memory_agent_accuracy)} good />
            <Metric label="Baseline (no memory)" value={pct(report.baseline_no_memory_accuracy)} />
            <Metric label="Baseline (full history)" value={pct(report.baseline_full_history_accuracy)} />
            <Metric label="Baseline (history summary)" value={pct(report.baseline_history_summary_accuracy)} />
            <Metric label={`Recall in context (top ${report.retrieval_top_k})`} value={pct(report.memory_recall_at_context)} good />
            <Metric label="Token savings" value={`${report.token_savings_percent}%`} good />
            <Metric label="Outdated mem errors" value={`${report.outdated_memory_errors}`} good={report.outdated_memory_errors === 0} />
            <Metric label="Avg retrieval" value={`${report.avg_retrieval_latency_ms} ms`} />
          </div>

          {report.provider_status !== "online" && (
            <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              This run used provider status <strong>{report.provider_status}</strong>.
              {report.provider_fallbacks > 0 && ` ${report.provider_fallbacks} provider calls fell back.`}
              Use an online Qwen run as final submission evidence.
            </p>
          )}

          <ComparisonBar
            agent={report.memory_agent_accuracy}
            noMemory={report.baseline_no_memory_accuracy}
            fullHistory={report.baseline_full_history_accuracy}
            historySummary={report.baseline_history_summary_accuracy}
          />

          {report.provider_token_usage.totals.total_tokens !== undefined && (
            <p className="mt-3 text-xs text-slate-400">
              Provider-reported tokens for this run: {report.provider_token_usage.totals.total_tokens.toLocaleString()}.
              Pricing is intentionally not estimated because model rates change.
            </p>
          )}

          <table className="mt-4 w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase text-slate-400">
                <th className="py-1">Scenario</th>
                <th>Agent</th>
                <th>No mem</th>
                <th>History</th>
                <th>Summary</th>
                <th>Tokens</th>
                <th>Leak</th>
              </tr>
            </thead>
            <tbody>
              {report.scenarios.map((s) => (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="py-1.5 text-slate-700">{s.title}</td>
                  <td title={s.answer_failure_reason ?? "Answer passed deterministic grading"}>
                    <Mark ok={s.memory_agent_correct} />
                  </td>
                  <td><Mark ok={s.baseline_correct} /></td>
                  <td><Mark ok={s.full_history_correct} /></td>
                  <td><Mark ok={s.history_summary_correct} /></td>
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

function ComparisonBar({
  agent,
  noMemory,
  fullHistory,
  historySummary,
}: {
  agent: number;
  noMemory: number;
  fullHistory: number;
  historySummary: number;
}) {
  return (
    <div className="space-y-2">
      <Row label="Memory agent" value={agent} color="bg-brand-500" />
      <Row label="No-memory baseline" value={noMemory} color="bg-slate-300" />
      <Row label="Full-history baseline" value={fullHistory} color="bg-slate-400" />
      <Row label="History-summary baseline" value={historySummary} color="bg-slate-500" />
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
