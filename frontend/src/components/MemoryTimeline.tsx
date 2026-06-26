import { useEffect, useState } from "react";
import { api, type TimelineEvent } from "../api";

// Each event kind gets a distinct dot colour on the timeline rail.
const KIND_COLOR: Record<string, string> = {
  created: "bg-emerald-500",
  updated: "bg-sky-500",
  superseded: "bg-rose-500",
  expired: "bg-orange-500",
  archived: "bg-slate-400",
  deleted: "bg-zinc-400",
  pinned: "bg-amber-500",
};

export function MemoryTimeline({ refreshKey }: { refreshKey: number }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.timeline().then((r) => setEvents(r.events)).catch(() => setEvents([]));
  }, [refreshKey]);

  const kinds = Array.from(new Set(events.map((e) => e.kind)));
  const shown = filter === "all" ? events : events.filter((e) => e.kind === filter);

  return (
    <div className="glass p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Memory Timeline</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white/70 px-2 py-1 text-xs"
        >
          <option value="all">all events</option>
          {kinds.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </div>

      {shown.length === 0 && (
        <p className="text-sm text-slate-400">No memory events yet.</p>
      )}

      <ol className="relative space-y-3 border-l border-slate-200 pl-4">
        {shown.map((e, i) => (
          <li key={i} className="relative animate-fade-up" style={{ animationDelay: `${Math.min(i, 8) * 0.05}s` }}>
            <span className="absolute -left-[23px] top-3 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-white shadow ring-2 ring-white">
              <span className={`h-2.5 w-2.5 rounded-full ${KIND_COLOR[e.kind] || "bg-slate-400"}`} />
            </span>
            <div className="card-hover rounded-xl border border-slate-200 bg-white/60 p-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-500">
                  {e.kind} · {e.type}
                </span>
                <span className="text-[11px] text-slate-400">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="mt-0.5 text-sm text-slate-700">{e.content}</p>
              {e.reason && (
                <p className="mt-0.5 text-[11px] text-slate-400">{e.reason}</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
