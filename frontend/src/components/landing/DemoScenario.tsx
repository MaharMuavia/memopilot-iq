import { Link } from "react-router-dom";

const STEPS = [
  { n: 1, title: "User gives preferences", body: "“I prefer FastAPI, React + Vite, Alibaba Cloud. Never commit API keys.”" },
  { n: 2, title: "Agent stores memories", body: "Structured records created — preferences, project, and a critical rule." },
  { n: 3, title: "User asks later", body: "“Design the backend architecture.” — a new session entirely." },
  { n: 4, title: "Agent recalls memories", body: "Relevant preferences are retrieved within budget; the critical rule is pinned." },
  { n: 5, title: "User changes preference", body: "“Actually, use Next.js instead of React + Vite.”" },
  { n: 6, title: "Agent supersedes", body: "The old React + Vite memory is superseded and never used again." },
];

export function DemoScenario() {
  return (
    <section id="demo" className="mx-auto max-w-6xl px-4 py-16">
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          See memory work end to end
        </h2>
        <p className="mt-3 text-slate-600">
          A scripted six-step flow shows creation, cross-session recall, and
          supersession — all visible in the Memory Trace.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((s) => (
          <div key={s.n} className="glass p-5">
            <div className="flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-600 text-xs font-bold text-white">
                {s.n}
              </span>
              <h3 className="text-sm font-semibold text-slate-800">{s.title}</h3>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 text-center">
        <Link to="/app" className="btn-primary px-5 py-2.5 text-base">
          Try scripted demo →
        </Link>
      </div>
    </section>
  );
}
