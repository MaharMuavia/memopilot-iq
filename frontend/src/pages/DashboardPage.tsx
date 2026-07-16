import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  DEFAULT_PROJECT,
  DEFAULT_USER,
  type ChatResponse,
  type HealthInfo,
} from "../api";
import { GITHUB_URL } from "../config";
import { ChatPanel } from "../components/ChatPanel";
import { MemoryTracePanel } from "../components/MemoryTracePanel";
import { MemoryTimeline } from "../components/MemoryTimeline";
import { MemoryControls } from "../components/MemoryControls";
import { EvaluationDashboard } from "../components/EvaluationDashboard";
import { JudgeDemoPanel } from "../components/JudgeDemoPanel";
import { SettingsPanel } from "../components/SettingsPanel";
import { MemoryGraph } from "../components/MemoryGraph";
import { AnalyticsPanel } from "../components/AnalyticsPanel";
import { ModeBadge } from "../components/StatusBadge";
import {
  IconChat, IconTrace, IconGraph, IconTimeline, IconAnalytics,
  IconEval, IconControls, IconSettings, IconHome, IconGithub,
} from "../components/icons";
import type { ComponentType, SVGProps } from "react";

type Tab =
  | "chat" | "trace" | "graph" | "timeline"
  | "analytics" | "eval" | "controls" | "settings";

type IconCmp = ComponentType<SVGProps<SVGSVGElement> & { size?: number }>;

const TABS: { id: Tab; label: string; Icon: IconCmp }[] = [
  { id: "chat", label: "Chat", Icon: IconChat },
  { id: "trace", label: "Memory Trace", Icon: IconTrace },
  { id: "graph", label: "Graph", Icon: IconGraph },
  { id: "timeline", label: "Timeline", Icon: IconTimeline },
  { id: "analytics", label: "Analytics", Icon: IconAnalytics },
  { id: "eval", label: "Evaluation", Icon: IconEval },
  { id: "controls", label: "Controls", Icon: IconControls },
  { id: "settings", label: "Settings", Icon: IconSettings },
];

export default function DashboardPage() {
  const [tab, setTab] = useState<Tab>("chat");
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [healthLoaded, setHealthLoaded] = useState(false);
  const [last, setLast] = useState<ChatResponse | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  // Keep a conversation session stable across state updates and rerenders.
  const sessionId = useRef(
    "session-" + new Date().toISOString().slice(11, 19).replace(/:/g, "")
  ).current;

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setHealthLoaded(true));
  }, []);

  function onActivity(resp: ChatResponse) {
    setLast(resp);
    setRefreshKey((k) => k + 1);
  }

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-1 text-xs text-slate-400 transition hover:text-brand-600"
              title="Back to landing page"
            >
              <IconHome size={15} /> Home
            </Link>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <span className="grid h-8 w-8 place-items-center rounded-xl bg-brand-600 text-sm font-bold text-white">
                M
              </span>
              <div>
                <h1 className="text-sm font-bold leading-tight text-slate-800">
                  MemoPilot <span className="text-brand-600">IQ</span>
                </h1>
                <p className="text-[11px] leading-tight text-slate-400">
                  {DEFAULT_PROJECT} · {sessionId}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <StatusBadges health={health} healthLoaded={healthLoaded} />
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="btn-ghost py-1.5 text-xs"
            >
              <IconGithub size={15} /> GitHub
            </a>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-6">
        {/* Judge demo — the headline proof of MemoryOS */}
        <JudgeDemoPanel onComplete={() => setRefreshKey((k) => k + 1)} />

        {/* Tabs */}
        <nav className="mb-5 flex flex-wrap gap-1.5">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`btn ${
                tab === id
                  ? "tab-active bg-brand-600 text-white"
                  : "bg-white/70 text-slate-600 border border-slate-200 hover:bg-white"
              }`}
            >
              <Icon size={16} className={tab === id ? "opacity-100" : "opacity-70"} />
              {label}
            </button>
          ))}
        </nav>

        <main key={tab} className="animate-fade-in">
          {tab === "chat" && (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="h-[72vh]">
                <ChatPanel sessionId={sessionId} onActivity={onActivity} />
              </div>
              <div className="max-h-[72vh] overflow-y-auto">
                <MemoryTracePanel last={last} />
              </div>
            </div>
          )}
          {tab === "trace" && <MemoryTracePanel last={last} />}
          {tab === "graph" && <MemoryGraph refreshKey={refreshKey} />}
          {tab === "timeline" && <MemoryTimeline refreshKey={refreshKey} />}
          {tab === "analytics" && (
            <AnalyticsPanel
              refreshKey={refreshKey}
              onChange={() => setRefreshKey((k) => k + 1)}
            />
          )}
          {tab === "eval" && <EvaluationDashboard />}
          {tab === "controls" && (
            <MemoryControls
              refreshKey={refreshKey}
              onChange={() => setRefreshKey((k) => k + 1)}
            />
          )}
          {tab === "settings" && (
            <SettingsPanel health={health} sessionId={sessionId} />
          )}
        </main>

        <footer className="mt-10 border-t border-slate-200/70 pt-4 text-center text-xs text-slate-400">
          Qwen Cloud Global AI Hackathon · Track 1: MemoryAgent ·{" "}
          {health ? `store: ${health.memory_store}` : "backend offline"}
        </footer>
      </div>
    </div>
  );
}

function StatusBadges({
  health,
  healthLoaded,
}: {
  health: HealthInfo | null;
  healthLoaded: boolean;
}) {
  if (!healthLoaded) {
    return <span className="chip bg-slate-100 text-slate-500">connecting…</span>;
  }
  if (!health) {
    return <span className="chip bg-rose-100 text-rose-700">backend offline</span>;
  }
  const cloud = health.memory_store.includes("alibaba");
  const qwenOnline = health.qwen_provider_status === "online";
  const qwenFallback = health.qwen_provider_status === "degraded_offline_fallback";
  return (
    <>
      <ModeBadge mode={health.mode} />
      <span
        className={`chip ${
          qwenOnline
            ? "bg-emerald-100 text-emerald-700"
            : "bg-slate-200 text-slate-600"
        }`}
        title={
          qwenOnline
            ? `Qwen online · ${health.qwen_model}`
            : "Qwen offline — deterministic local fallback"
        }
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            qwenOnline ? "bg-emerald-500" : "bg-slate-400"
          }`}
        />
        {qwenOnline ? "Qwen Online" : qwenFallback ? "Qwen Fallback" : "Qwen Offline"}
      </span>
      <span
        className={`chip ${cloud ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-700"}`}
        title={`Memory store: ${health.memory_store}`}
      >
        {cloud ? "Alibaba Store" : "SQLite"}
      </span>
    </>
  );
}
