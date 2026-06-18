const FLOW = [
  { label: "User", icon: "👤", tone: "slate" },
  { label: "React Frontend", icon: "⚛️", tone: "blue" },
  { label: "FastAPI Backend", icon: "⚡", tone: "blue" },
  { label: "MemoryOS", icon: "🧠", tone: "indigo" },
  { label: "Qwen Cloud", icon: "☁️", tone: "orange" },
  { label: "Alibaba Memory Store / OSS", icon: "🗃️", tone: "amber" },
  { label: "Memory Trace Dashboard", icon: "🪞", tone: "cyan" },
];

const TONES: Record<string, string> = {
  slate: "bg-white border-slate-200 text-slate-700",
  blue: "bg-blue-50 border-blue-200 text-blue-800",
  indigo: "bg-indigo-50 border-indigo-200 text-indigo-800",
  orange: "bg-orange-50 border-orange-200 text-orange-800",
  amber: "bg-amber-50 border-amber-200 text-amber-800",
  cyan: "bg-cyan-50 border-cyan-200 text-cyan-800",
};

export function ArchitectureFlow() {
  return (
    <section id="architecture" className="bg-gradient-to-b from-transparent to-brand-50/40">
      <div className="mx-auto max-w-6xl px-4 py-16">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">
            How a request flows
          </h2>
          <p className="mt-3 text-slate-600">
            Every message passes through the MemoryOS layer before and after the
            model call.
          </p>
        </div>

        <div className="flex flex-wrap items-stretch justify-center gap-3">
          {FLOW.map((node, i) => (
            <div key={node.label} className="flex items-center gap-3">
              <div
                className={`flex min-w-[150px] flex-col items-center rounded-2xl border px-5 py-4 text-center shadow-glass ${TONES[node.tone]}`}
              >
                <span className="text-2xl">{node.icon}</span>
                <span className="mt-1.5 text-sm font-semibold">{node.label}</span>
              </div>
              {i < FLOW.length - 1 && (
                <span className="hidden text-2xl text-slate-300 md:inline">→</span>
              )}
            </div>
          ))}
        </div>

        <p className="mx-auto mt-8 max-w-3xl text-center text-sm text-slate-500">
          Runs in <strong>LOCAL_MODE</strong> (SQLite + local vectors) with no
          keys, and upgrades to <strong>ALIBABA_CLOUD_MODE</strong> (Tablestore +
          OSS) automatically when cloud credentials are present.
        </p>
      </div>
    </section>
  );
}
