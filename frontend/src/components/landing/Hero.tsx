import { Link } from "react-router-dom";
import { IconSparkle } from "../icons";

const BADGES = [
  "Track 1: MemoryAgent",
  "Qwen Cloud API",
  "Alibaba Cloud Ready",
  "Persistent Memory",
  "Intelligent Forgetting",
  "Memory Trace",
];

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      {/* soft gradient backdrop */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(1100px 520px at 80% -8%, #dbeafe 0%, transparent 60%), radial-gradient(800px 420px at -5% 10%, #ede9fe 0%, transparent 55%)",
        }}
      />
      <div className="stagger mx-auto max-w-6xl px-4 py-20 text-center md:py-28">
        <div>
          <span className="chip mb-5 inline-flex items-center gap-1.5 bg-white/70 text-brand-700 shadow-glass">
            <IconSparkle size={14} /> Memory intelligence for AI agents
          </span>
        </div>
        <h1 className="mx-auto max-w-3xl text-4xl font-extrabold tracking-tight text-slate-900 md:text-6xl">
          MemoPilot <span className="text-brand-600">IQ</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-slate-600 md:text-lg">
          A persistent-memory AI agent that learns your preferences, remembers
          project decisions, forgets outdated information, and explains every
          memory it uses.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link to="/app" className="btn-primary px-5 py-2.5 text-base">
            Launch MemoryOS →
          </Link>
          <Link to="/app" className="btn-ghost px-5 py-2.5 text-base">
            Try Judge Demo
          </Link>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
          {BADGES.map((b) => (
            <span
              key={b}
              className="chip border border-slate-200 bg-white/70 text-slate-600"
            >
              {b}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
