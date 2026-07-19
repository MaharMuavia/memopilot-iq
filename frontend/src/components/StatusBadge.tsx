import type { MemoryStatus, MemoryType } from "../api";

const STATUS_STYLES: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-700",
  pinned: "bg-amber-100 text-amber-800",
  archived: "bg-slate-200 text-slate-600",
  expired: "bg-orange-100 text-orange-700",
  superseded: "bg-rose-100 text-rose-700",
  deleted: "bg-zinc-200 text-zinc-500 line-through",
};

const TYPE_STYLES: Record<string, string> = {
  preference: "bg-blue-100 text-blue-700",
  project: "bg-indigo-100 text-indigo-700",
  decision: "bg-violet-100 text-violet-700",
  constraint: "bg-cyan-100 text-cyan-700",
  deadline: "bg-orange-100 text-orange-700",
  mistake: "bg-rose-100 text-rose-700",
  learning_goal: "bg-teal-100 text-teal-700",
  task: "bg-sky-100 text-sky-700",
  critical: "bg-red-100 text-red-700",
  temporary: "bg-slate-100 text-slate-600",
};

export function StatusBadge({ status }: { status: MemoryStatus }) {
  return (
    <span className={`chip ${STATUS_STYLES[status] || "bg-slate-100 text-slate-600"}`}>
      {status}
    </span>
  );
}

export function TypeBadge({ type }: { type: MemoryType }) {
  return (
    <span className={`chip ${TYPE_STYLES[type] || "bg-slate-100 text-slate-600"}`}>
      {type}
    </span>
  );
}

export function ModeBadge({ mode }: { mode: string }) {
  const cloud = mode === "ALIBABA_CLOUD_MODE";
  return (
    <span
      className={`chip ${cloud ? "bg-orange-100 text-orange-700" : "bg-emerald-100 text-emerald-700"}`}
      title={cloud ? "Persisting to Alibaba Cloud" : "Running with local development storage"}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${cloud ? "bg-orange-500" : "bg-emerald-500"}`} />
      {cloud ? "Alibaba Cloud" : "Local"}
    </span>
  );
}
