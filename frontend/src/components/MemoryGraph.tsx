import { useEffect, useMemo, useState } from "react";
import { api, type GraphData, type GraphNode } from "../api";

const TYPE_COLOR: Record<string, string> = {
  preference: "#3b82f6",
  project: "#6366f1",
  decision: "#8b5cf6",
  constraint: "#06b6d4",
  deadline: "#f97316",
  mistake: "#f43f5e",
  learning_goal: "#14b8a6",
  task: "#0ea5e9",
  critical: "#ef4444",
  temporary: "#94a3b8",
};

const W = 720;
const H = 520;
const CX = W / 2;
const CY = H / 2;

export function MemoryGraph({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<GraphData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.graph().then(setData).catch((e) => setError(String(e)));
  }, [refreshKey]);

  const positions = useMemo(() => {
    const pos: Record<string, { x: number; y: number }> = {};
    if (!data) return pos;
    const n = data.nodes.length || 1;
    const radius = Math.min(W, H) / 2 - 70;
    data.nodes.forEach((node, i) => {
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      pos[node.id] = {
        x: CX + radius * Math.cos(angle),
        y: CY + radius * Math.sin(angle),
      };
    });
    return pos;
  }, [data]);

  if (error) {
    return <div className="glass p-4 text-sm text-rose-600">Could not load graph: {error}</div>;
  }
  if (!data) {
    return <div className="glass p-4 text-sm text-slate-500">Loading memory graph…</div>;
  }
  if (data.nodes.length === 0) {
    return (
      <div className="glass p-6 text-center text-sm text-slate-500">
        No memories yet. Run the Judge Demo or chat to populate the graph.
      </div>
    );
  }

  const neighbors = new Set<string>();
  if (selected) {
    data.edges.forEach((e) => {
      if (e.source === selected) neighbors.add(e.target);
      if (e.target === selected) neighbors.add(e.source);
    });
  }
  const selectedNode = data.nodes.find((n) => n.id === selected) || null;

  function nodeOpacity(node: GraphNode) {
    if (["superseded", "archived", "expired"].includes(node.status)) return 0.35;
    if (selected && node.id !== selected && !neighbors.has(node.id)) return 0.25;
    return 1;
  }

  return (
    <div className="glass p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-700">Live Memory Graph</h2>
          <p className="text-xs text-slate-400">
            {data.nodes.length} memories · {data.edges.length} links · click a node to focus
          </p>
        </div>
        <Legend />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_240px]">
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white/60">
          <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" onClick={() => setSelected(null)}>
            {/* edges */}
            {data.edges.map((e, i) => {
              const a = positions[e.source];
              const b = positions[e.target];
              if (!a || !b) return null;
              const active =
                !selected || e.source === selected || e.target === selected;
              const isSupersede = e.kind === "supersedes";
              return (
                <line
                  key={i}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={isSupersede ? "#f43f5e" : "#cbd5e1"}
                  strokeWidth={isSupersede ? 2 : 1}
                  strokeDasharray={isSupersede ? "5 4" : undefined}
                  opacity={active ? (isSupersede ? 0.9 : 0.5) : 0.08}
                />
              );
            })}

            {/* nodes */}
            {data.nodes.map((node) => {
              const p = positions[node.id];
              if (!p) return null;
              const r = 9 + node.importance * 9;
              const color = node.is_insight ? "#eab308" : TYPE_COLOR[node.type] || "#64748b";
              return (
                <g
                  key={node.id}
                  transform={`translate(${p.x},${p.y})`}
                  opacity={nodeOpacity(node)}
                  style={{ cursor: "pointer" }}
                  onClick={(ev) => {
                    ev.stopPropagation();
                    setSelected(node.id === selected ? null : node.id);
                  }}
                >
                  {node.is_critical && (
                    <circle r={r + 4} fill="none" stroke="#ef4444" strokeWidth={2} />
                  )}
                  <circle r={r} fill={color} stroke="white" strokeWidth={2} />
                  {node.is_insight && (
                    <text textAnchor="middle" dy="4" fontSize="11" fill="white">★</text>
                  )}
                  <title>{`[${node.type}/${node.status}] ${node.label}`}</title>
                </g>
              );
            })}
          </svg>
        </div>

        <aside className="rounded-xl border border-slate-200 bg-white/60 p-3 text-sm">
          {selectedNode ? (
            <div>
              <div className="mb-1 flex items-center gap-1.5">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ background: selectedNode.is_insight ? "#eab308" : TYPE_COLOR[selectedNode.type] }}
                />
                <span className="text-xs font-semibold uppercase text-slate-500">
                  {selectedNode.type}
                </span>
              </div>
              <p className="text-slate-700">{selectedNode.label}</p>
              <dl className="mt-2 space-y-1 text-xs text-slate-500">
                <div className="flex justify-between"><dt>Status</dt><dd>{selectedNode.status}</dd></div>
                <div className="flex justify-between"><dt>Importance</dt><dd>{selectedNode.importance.toFixed(2)}</dd></div>
                <div className="flex justify-between"><dt>Critical</dt><dd>{selectedNode.is_critical ? "yes" : "no"}</dd></div>
                <div className="flex justify-between"><dt>Links</dt><dd>{neighbors.size}</dd></div>
              </dl>
              {selectedNode.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedNode.tags.map((t) => (
                    <span key={t} className="chip bg-slate-100 text-slate-500">{t}</span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-400">
              Click any node to inspect its type, status, importance, and links.
              Red dashed edges = supersession; gold ★ = reflection insight.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}

function Legend() {
  const items = [
    { c: "#3b82f6", l: "preference" },
    { c: "#8b5cf6", l: "decision" },
    { c: "#ef4444", l: "critical" },
    { c: "#eab308", l: "insight ★" },
    { c: "#f43f5e", l: "supersedes —" },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((it) => (
        <span key={it.l} className="flex items-center gap-1 text-[11px] text-slate-500">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: it.c }} />
          {it.l}
        </span>
      ))}
    </div>
  );
}
