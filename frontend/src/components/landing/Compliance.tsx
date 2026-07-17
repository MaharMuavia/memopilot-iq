import { IconCheck } from "../icons";

const CHECKS = [
  "Uses Qwen Cloud API",
  "Supports persistent memory",
  "Recalls critical memories in limited context",
  "Forgets outdated memories",
  "Provides Alibaba Cloud deployment path",
  "Includes evaluation dashboard",
];

export function Compliance() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16">
      <div className="glass overflow-hidden p-8 md:p-10">
        <div className="grid items-center gap-8 md:grid-cols-2">
          <div>
            <span className="chip mb-3 bg-brand-50 text-brand-700">Hackathon</span>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
              Built for Qwen Cloud Track 1: MemoryAgent
            </h2>
            <p className="mt-3 text-slate-600">
              The core MemoryAgent requirements are implemented and verifiable
              in the app and repository. Final live-cloud evidence is tracked
              explicitly in the submission release gate.
            </p>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {CHECKS.map((c) => (
              <li
                key={c}
                className="flex items-start gap-2 rounded-xl border border-slate-200 bg-white/70 p-3 text-sm text-slate-700"
              >
                <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700">
                  <IconCheck size={13} />
                </span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
