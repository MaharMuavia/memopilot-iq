import { useState } from "react";
import { api, type ChatResponse, type MemoryRecord } from "../api";
import { TypeBadge } from "./StatusBadge";

interface Turn {
  role: "user" | "assistant";
  text: string;
  used?: MemoryRecord[];
  actions?: ChatResponse["memory_actions"];
}

const STARTERS = [
  "I prefer FastAPI backend, React + Vite, Alibaba Cloud, light UI, and short answers. Never commit API keys.",
  "Design the backend architecture.",
  "Actually, I changed my mind. Use Next.js instead of React + Vite.",
  "What stack should I use now and what should I show judges?",
];

export function ChatPanel({
  sessionId,
  onActivity,
}: {
  sessionId: string;
  onActivity: (resp: ChatResponse) => void;
}) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(message: string) {
    if (!message.trim() || loading) return;
    setError(null);
    setTurns((t) => [...t, { role: "user", text: message }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await api.chat(message, sessionId);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          text: resp.answer,
          used: resp.used_memories,
          actions: resp.memory_actions,
        },
      ]);
      onActivity(resp);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass flex h-full flex-col p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Chat</h2>
        <span className="text-xs text-slate-400">session {sessionId}</span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {turns.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-slate-500">
              Try the scripted demo — send these in order to watch memory get
              created, recalled, then superseded:
            </p>
            {STARTERS.map((s, i) => (
              <button
                key={i}
                onClick={() => send(s)}
                className="block w-full rounded-xl border border-slate-200 bg-white/60 px-3 py-2 text-left text-sm text-slate-600 hover:bg-white"
              >
                {i + 1}. {s}
              </button>
            ))}
          </div>
        )}

        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${
                t.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-700 border border-slate-200"
              }`}
            >
              {t.text}
            </div>
            {t.role === "assistant" && t.used && t.used.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                <span className="text-[11px] text-slate-400">memory used:</span>
                {t.used.slice(0, 6).map((m) => (
                  <span
                    key={m.memory_id}
                    title={m.content}
                    className="chip bg-brand-50 text-brand-700"
                  >
                    <TypeBadge type={m.type} />
                    {m.summary.slice(0, 28)}
                  </span>
                ))}
              </div>
            )}
            {t.role === "assistant" && t.actions && (
              <ActionSummary actions={t.actions} />
            )}
          </div>
        ))}
        {loading && <div className="text-sm text-slate-400">MemoPilot is thinking…</div>}
      </div>

      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}

      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Tell MemoPilot a preference, decision, or ask a question…"
          className="flex-1 rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm outline-none focus:border-brand-500"
        />
        <button className="btn-primary" onClick={() => send(input)} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

function ActionSummary({ actions }: { actions: ChatResponse["memory_actions"] }) {
  const parts: string[] = [];
  if (actions.created.length) parts.push(`+${actions.created.length} created`);
  if (actions.superseded.length) parts.push(`↻${actions.superseded.length} superseded`);
  if (actions.updated.length) parts.push(`~${actions.updated.length} merged`);
  if (actions.forgotten.length) parts.push(`–${actions.forgotten.length} forgotten`);
  if (actions.redacted.length) parts.push(`secret redacted`);
  if (parts.length === 0) return null;
  return <div className="mt-1 text-[11px] text-slate-400">{parts.join(" · ")}</div>;
}
