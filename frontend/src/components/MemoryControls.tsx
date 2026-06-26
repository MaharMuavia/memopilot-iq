import { useEffect, useState } from "react";
import { api, type MemoryRecord } from "../api";
import { StatusBadge, TypeBadge } from "./StatusBadge";
import { IconArchive, IconDownload, IconPin, IconTrash } from "./icons";

export function MemoryControls({
  refreshKey,
  onChange,
}: {
  refreshKey: number;
  onChange: () => void;
}) {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    try {
      const r = await api.listMemories(true);
      setMemories(r.memories);
    } catch {
      setMemories([]);
    }
  }

  useEffect(() => {
    load();
  }, [refreshKey]);

  async function act(fn: () => Promise<unknown>, id: string) {
    setBusy(id);
    try {
      await fn();
      await load();
      onChange();
    } finally {
      setBusy(null);
    }
  }

  async function exportJson() {
    const data = await api.exportMemories();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "memopilot-memories.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function forgetAll() {
    if (!confirm("Forget ALL memories for this project? They will be cleared.")) return;
    await api.forgetAll();
    await load();
    onChange();
  }

  return (
    <div className="glass p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">
          Memory Controls ({memories.length})
        </h2>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={exportJson}>
            <IconDownload size={15} /> Export JSON
          </button>
          <button
            className="btn bg-rose-600 text-white hover:bg-rose-700"
            onClick={forgetAll}
          >
            <IconTrash size={15} /> Forget all
          </button>
        </div>
      </div>

      <div className="stagger space-y-2">
        {memories.length === 0 && (
          <p className="text-sm text-slate-400">No memories stored yet.</p>
        )}
        {memories.map((m) => (
          <div
            key={m.memory_id}
            className="card-hover rounded-xl border border-slate-200 bg-white/60 p-2.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-wrap items-center gap-1.5">
                <TypeBadge type={m.type} />
                <StatusBadge status={m.status} />
                {m.is_critical && (
                  <span className="chip bg-red-100 text-red-700">critical</span>
                )}
              </div>
              <span className="font-mono text-[11px] text-slate-400">
                imp {m.importance.toFixed(2)} · used {m.usage_count}×
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-700">{m.content}</p>
            {m.reason && (
              <p className="mt-0.5 text-[11px] text-slate-400">{m.reason}</p>
            )}
            <div className="mt-2 flex gap-2">
              <button
                className="btn-ghost py-1 text-xs"
                disabled={busy === m.memory_id}
                onClick={() => act(() => api.pin(m.memory_id), m.memory_id)}
              >
                <IconPin size={14} /> Pin
              </button>
              <button
                className="btn-ghost py-1 text-xs"
                disabled={busy === m.memory_id}
                onClick={() => act(() => api.archive(m.memory_id), m.memory_id)}
              >
                <IconArchive size={14} /> Archive
              </button>
              <button
                className="btn-ghost py-1 text-xs text-rose-600"
                disabled={busy === m.memory_id}
                onClick={() => act(() => api.remove(m.memory_id), m.memory_id)}
              >
                <IconTrash size={14} /> Forget
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
