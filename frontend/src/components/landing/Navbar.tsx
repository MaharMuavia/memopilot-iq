import { Link } from "react-router-dom";
import { GITHUB_URL } from "../../config";

const LINKS = [
  { href: "#features", label: "Features" },
  { href: "#architecture", label: "Architecture" },
  { href: "#demo", label: "Demo" },
  { href: "#evaluation", label: "Evaluation" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/60 bg-white/75 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <a href="#top" className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-600 text-base font-bold text-white shadow-glass">
            M
          </span>
          <span className="text-lg font-bold tracking-tight text-slate-800">
            MemoPilot <span className="text-brand-600">IQ</span>
          </span>
        </a>

        <div className="hidden items-center gap-6 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-slate-600 transition hover:text-brand-600"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost hidden sm:inline-flex"
          >
            GitHub
          </a>
          <Link to="/app" className="btn-primary">
            Launch App
          </Link>
        </div>
      </nav>
    </header>
  );
}
