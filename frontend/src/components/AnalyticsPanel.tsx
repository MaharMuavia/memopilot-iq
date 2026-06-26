import { useEffect, useState } from "react";
import { api, type AnalyticsReport, type ReflectionReport } from "../api";
import { IconSparkle } from "./icons";

const TYPE_COLOR: Record<string, string> = {
  preference: "#3b82f6", project: "#6366f1", decision: "#8b5cf6",
  constraint: "#06b6d4", deadline: "#f97316", mistake: "#f43f5e",
  learning_goal: "#14b8a6", task: "#0ea5e9", critical: "#ef4444",
  temporary: "#94a3b8",
};

export function AnalyticsPanel({
  refreshKey,
  onChange,
}: {
  refreshKey: number;
  onChange: () => void;
}) {
  const [data, setData] = useState<AnalyticsReport | null>(null);
  const [reflection, setReflection] = useState<ReflectionReport | null>(null);
  const [reflecting, setReflecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setData(await api.analytics());
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    load();
  }, [refreshKey]);

  async function runReflection() {
    setReflecting(true);
    setError(null);
    try {
      const r = await api.reflect();
      setReflection(r);
      await load();
      onChange();
    } catch (e) {
      setError(String(e));
    } finally {
      setReflecting(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Reflection engine */}
      <div className="overflow-hidden rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-yellow-50 shadow-glass">
        <div className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-amber-500 text-white shadow-glass">
              <IconSparkle size={16} />
            </span>
            <div>
              <h3 className="text-sm font-bold text-slate-800">Memory Reflection (self-improvement)</h3>
              <p className="text-xs text-slate-500">
                Consolidates duplicates, promotes frequently-used memories, and
                derives higher-level insights.
              </p>
            </div>
          </div>
          <button className="btn-primary px-4 py-2 text-sm" onClick={runReflection} disabled={reflecting}>
            {reflecting ? "Reflecting…" : "Run Reflection"}
          </button>
        </div>
        {reflection && (
          <div className="grid gap-3 border-t border-amber-200/70 bg-white/70 p-4 sm:grid-cols-4">
            <Stat label="Reviewed" value={reflection.reviewed} />
            <Stat label="Merged" value={reflection.merged.length} tone="text-cyan-600" />
            <Stat label="Promoted" value={reflection.promoted.length} tone="text-emerald-600" />
            <Stat label="Insights derived" value={reflection.insights.length} tone="text-amber-600" />
            {reflection.insights.length > 0 && (
              <ul className="sm:col-span-4 space-y-1 text-xs text-slate-600">
                {reflection.insights.map((i) => (
                  <li key={i.memory_id}>★ {i.summary}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {error && <p className="text-xs text-rose-600">{error}</p>}

      {data && (
        <>
          <div className="stagger grid grid-cols-2 gap-3 md:grid-cols-6">
            <Metric label="Total" value={data.totals.total} />
            <Metric label="Active" value={data.totals.active} tone="text-emerald-600" />
            <Metric label="Superseded" value={data.totals.superseded} tone="text-rose-600" />
            <Metric label="Expired" value={data.totals.expired} tone="text-orange-600" />
            <Metric label="Critical" value={data.totals.critical} tone="text-red-600" />
            <Metric
              label="Token savings"
              value={data.token_savings_percent != null ? `${data.token_savings_percent}%` : "—"}
              tone="text-brand-600"
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="glass p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-700">Memories by type</h3>
              <BarChart counts={data.type_counts} colorFor={(k) => TYPE_COLOR[k] || "#64748b"} />
            </div>
            <div className="glass p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-700">Memory events</h3>
              <BarChart counts={data.event_kind_counts} colorFor={() => "#6366f1"} />
            </div>
          </div>

          <div className="glass p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">Cumulative memory growth</h3>
            <GrowthChart growth={data.growth} />
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 text-center">
      <div className={`text-2xl font-bold ${tone ?? "text-slate-700"}`}>{value}</div>
      <div className="text-[11px] text-slate-500">{label}</div>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="glass p-3 text-center">
      <div className={`text-xl font-bold ${tone ?? "text-slate-700"}`}>{value}</div>
      <div className="text-[11px] text-slate-500">{label}</div>
    </div>
  );
}

function BarChart({
  counts,
  colorFor,
}: {
  counts: Record<string, number>;
  colorFor: (key: string) => string;
}) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0) return <p className="text-sm text-slate-400">No data yet.</p>;
  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center gap-2">
          <span className="w-28 shrink-0 truncate text-xs text-slate-500">{key.replace(/_/g, " ")}</span>
          <div className="h-4 flex-1 rounded bg-slate-100">
            <div
              className="h-4 rounded"
              style={{ width: `${(value / max) * 100}%`, background: colorFor(key) }}
            />
          </div>
          <span className="w-6 text-right text-xs font-medium text-slate-600">{value}</span>
        </div>
      ))}
    </div>
  );
}

function GrowthChart({ growth }: { growth: { date: string; cumulative: number }[] }) {
  if (growth.length === 0) return <p className="text-sm text-slate-400">No data yet.</p>;
  const W = 600;
  const H = 140;
  const pad = 24;
  const max = Math.max(1, ...growth.map((g) => g.cumulative));
  const step = growth.length > 1 ? (W - pad * 2) / (growth.length - 1) : 0;
  const pts = growth.map((g, i) => {
    const x = pad + i * step;
    const y = H - pad - (g.cumulative / max) * (H - pad * 2);
    return `${x},${y}`;
  });
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
      <polyline points={pts.join(" ")} fill="none" stroke="#2563eb" strokeWidth={2} />
      {growth.map((g, i) => {
        const x = pad + i * step;
        const y = H - pad - (g.cumulative / max) * (H - pad * 2);
        return <circle key={i} cx={x} cy={y} r={3} fill="#2563eb" />;
      })}
      <text x={pad} y={H - 6} fontSize="10" fill="#94a3b8">{growth[0].date}</text>
      <text x={W - pad} y={H - 6} fontSize="10" fill="#94a3b8" textAnchor="end">
        {growth[growth.length - 1].date}
      </text>
    </svg>
  );
}
