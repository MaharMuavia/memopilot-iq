import { Link } from "react-router-dom";

const METRICS = [
  { label: "Memory Recall@5", value: "88%", tone: "text-emerald-600" },
  { label: "Outdated Memory Avoidance", value: "96%", tone: "text-emerald-600" },
  { label: "Token Savings", value: "60%", tone: "text-brand-600" },
  { label: "Preference Adherence", value: "91%", tone: "text-emerald-600" },
  { label: "Retrieval Latency", value: "120ms", tone: "text-slate-700" },
];

export function EvaluationPreview() {
  return (
    <section id="evaluation" className="bg-gradient-to-b from-brand-50/40 to-transparent">
      <div className="mx-auto max-w-6xl px-4 py-16">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">
            Measured, not just claimed
          </h2>
          <p className="mt-3 text-slate-600">
            A built-in benchmark compares the memory agent against a no-memory
            baseline. Representative results:
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          {METRICS.map((m) => (
            <div key={m.label} className="glass p-5 text-center">
              <div className={`text-3xl font-extrabold ${m.tone}`}>{m.value}</div>
              <div className="mt-1.5 text-xs font-medium text-slate-500">{m.label}</div>
            </div>
          ))}
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Run the live benchmark inside the{" "}
          <Link to="/app" className="font-semibold text-brand-600 hover:underline">
            Evaluation dashboard
          </Link>
          .
        </p>
      </div>
    </section>
  );
}
