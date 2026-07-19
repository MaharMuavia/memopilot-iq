import { DEFAULT_PROJECT, DEFAULT_USER, type HealthInfo } from "../api";
import { GITHUB_URL } from "../config";

export function SettingsPanel({
  health,
  sessionId,
}: {
  health: HealthInfo | null;
  sessionId: string;
}) {
  const rows: { label: string; value: string; tone?: string }[] = [
    { label: "Runtime mode", value: health?.mode ?? "—", tone: health?.mode === "ALIBABA_CLOUD_MODE" ? "text-orange-600" : "text-emerald-600" },
    { label: "Qwen status", value: health ? (health.qwen_configured ? `Online · ${health.qwen_model}` : "Offline (local fallback)") : "—" },
    { label: "Memory store", value: health?.memory_store ?? "—" },
    { label: "Storage schema", value: health?.storage_schema ?? "—" },
    { label: "Tenant isolation", value: health?.tenant_isolation ?? "—" },
    { label: "OSS configured", value: health ? (health.oss_configured ? "Yes" : "No (local snapshots)") : "—" },
    { label: "Context token budget", value: health ? String(health.token_budget) : "—" },
    { label: "Deployed revision", value: health?.build_sha?.slice(0, 12) ?? "—" },
    { label: "User ID", value: DEFAULT_USER },
    { label: "Project ID", value: DEFAULT_PROJECT },
    { label: "Session ID", value: sessionId },
  ];

  return (
    <div className="space-y-4">
      <div className="glass p-5">
        <h2 className="mb-1 text-sm font-semibold text-slate-700">Settings &amp; Environment</h2>
        <p className="mb-4 text-xs text-slate-500">
          Live configuration reported by the backend <code>/health</code> endpoint.
        </p>
        <dl className="grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2">
          {rows.map((r) => (
            <div key={r.label} className="flex items-center justify-between bg-white px-4 py-3">
              <dt className="text-sm text-slate-500">{r.label}</dt>
              <dd className={`text-sm font-medium ${r.tone ?? "text-slate-800"}`}>
                {r.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="glass p-5">
        <h3 className="mb-2 text-sm font-semibold text-slate-700">How to enable cloud mode</h3>
        <ol className="list-decimal space-y-1.5 pl-5 text-sm text-slate-600">
          <li>Set <code>QWEN_API_KEY</code> + <code>QWEN_BASE_URL</code> to go from Qwen Offline → Online.</li>
          <li>Set <code>MEMORY_STORE=alibaba</code> and the <code>ALIBABA_*</code> vars for Tablestore + OSS.</li>
          <li>Restart the backend — this page and the header badges update automatically.</li>
        </ol>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
          className="btn-ghost mt-4 inline-flex text-sm"
        >
          View setup docs on GitHub →
        </a>
      </div>
    </div>
  );
}
