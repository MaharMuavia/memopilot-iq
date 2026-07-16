import { Link } from "react-router-dom";
import { GITHUB_URL } from "../../config";

export function Footer() {
  return (
    <footer className="border-t border-slate-200/70 bg-white/60">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-4 py-10 md:flex-row md:items-start">
        <div className="text-center md:text-left">
          <div className="flex items-center justify-center gap-2 md:justify-start">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-brand-600 text-sm font-bold text-white">
              M
            </span>
            <span className="text-lg font-bold text-slate-800">
              MemoPilot <span className="text-brand-600">IQ</span>
            </span>
          </div>
          <p className="mt-2 max-w-sm text-sm text-slate-500">
            Qwen Cloud Global AI Hackathon · Track 1: MemoryAgent
          </p>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
          <a href="#architecture" className="text-slate-600 hover:text-brand-600">
            Architecture
          </a>
          <a href="#demo" className="text-slate-600 hover:text-brand-600">
            Demo
          </a>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="text-slate-600 hover:text-brand-600"
          >
            GitHub
          </a>
          <Link to="/app" className="btn-primary">
            Launch App
          </Link>
        </nav>
      </div>
      <div className="border-t border-slate-200/70 py-4 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} MemoPilot IQ — A self-curating
        persistent-memory agent.
      </div>
    </footer>
  );
}
