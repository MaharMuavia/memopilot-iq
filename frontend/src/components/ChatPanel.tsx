import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, type ChatResponse, type MemoryRecord } from "../api";
import { TypeBadge } from "./StatusBadge";

const ASSISTANT_MARKDOWN_ELEMENTS = [
  "p", "strong", "em", "ul", "ol", "li", "a", "code", "pre",
  "blockquote", "h1", "h2", "h3", "hr", "br", "table", "thead",
  "tbody", "tr", "th", "td",
] as const;

interface Turn {
  role: "user" | "assistant";
  text: string;
  used?: MemoryRecord[];
  actions?: ChatResponse["memory_actions"];
  providerFallback?: boolean;
}

const STARTERS = [
  "I prefer FastAPI backend, React + Vite, Alibaba Cloud, light UI, and short answers. Never commit API keys.",
  "Summarize MemoPilot IQ's currently deployed Alibaba Cloud architecture in five concise bullets. Use only implemented services; do not propose alternatives.",
  "For the next iteration after this submission, migrate the frontend to Next.js instead of React + Vite. Confirm this plan in two sentences.",
  "What frontend does this submitted build use today, and what is planned after submission?",
];

function memoryChipLabel(memory: MemoryRecord, maxLength = 48) {
  const label = (memory.summary || memory.content).trim();
  if (label.length <= maxLength) return label;
  return `${label.slice(0, maxLength - 1).trimEnd()}…`;
}

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
  const [guidedStep, setGuidedStep] = useState(0);

  async function send(message: string, starterIndex?: number) {
    if (!message.trim() || loading) return;
    setError(null);
    setTurns((current) => [...current, { role: "user", text: message }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await api.chat(message, sessionId);
      setTurns((current) => [
        ...current,
        {
          role: "assistant",
          text: resp.answer,
          used: resp.used_memories,
          actions: resp.memory_actions,
          providerFallback: resp.qwen_fallback_used,
        },
      ]);
      if (resp.qwen_fallback_used) {
        setError("Qwen timed out on this turn. The answer used the offline fallback; retry this guided step before recording.");
      } else if (starterIndex === guidedStep) {
        setGuidedStep((current) => Math.min(current + 1, STARTERS.length));
      }
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

      <GuidedDemo
        step={guidedStep}
        loading={loading}
        onRun={(message, index) => send(message, index)}
      />

      <div className="mt-3 flex-1 space-y-3 overflow-y-auto pr-1">
        {turns.map((turn, index) => (
          <div key={index} className={turn.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${
                turn.role === "user"
                  ? "bg-brand-600 text-white"
                  : "border border-slate-200 bg-white text-slate-700"
              }`}
            >
              {turn.role === "assistant" ? (
                <div className="chat-markdown">
                  <ReactMarkdown
                    allowedElements={ASSISTANT_MARKDOWN_ELEMENTS}
                    remarkPlugins={[remarkGfm]}
                    skipHtml
                  >
                    {turn.text}
                  </ReactMarkdown>
                </div>
              ) : turn.text}
            </div>
            {turn.role === "assistant" && turn.providerFallback && (
              <div className="mt-1.5 text-xs font-medium text-amber-700">
                Qwen provider timeout - offline fallback used for this answer.
              </div>
            )}
            {turn.role === "assistant" && turn.used && turn.used.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                <span className="text-[11px] text-slate-400">memory used:</span>
                {turn.used.slice(0, 6).map((memory) => (
                  <span key={memory.memory_id} title={memory.content} className="chip bg-brand-50 text-brand-700">
                    <TypeBadge type={memory.type} />
                    {memoryChipLabel(memory)}
                  </span>
                ))}
              </div>
            )}
            {turn.role === "assistant" && turn.actions && <ActionSummary actions={turn.actions} />}
          </div>
        ))}
        {loading && <div className="text-sm text-slate-400">MemoPilot is thinking...</div>}
      </div>

      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}

      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && send(input)}
          placeholder="Tell MemoPilot a preference, decision, or ask a question..."
          className="flex-1 rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm outline-none focus:border-brand-500"
        />
        <button className="btn-primary" onClick={() => send(input)} disabled={loading}>Send</button>
      </div>
    </div>
  );
}

function GuidedDemo({
  step,
  loading,
  onRun,
}: {
  step: number;
  loading: boolean;
  onRun: (message: string, index: number) => void;
}) {
  if (step >= STARTERS.length) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-xs text-emerald-800">
        Live Qwen memory flow complete: created, recalled, superseded, and verified.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-brand-200 bg-brand-50/70 p-3">
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold text-brand-700">Live demo step {step + 1} of {STARTERS.length}</span>
        <div className="flex gap-1" aria-label={`Demo progress: ${step} of ${STARTERS.length}`}>
          {STARTERS.map((_, index) => (
            <span
              key={index}
              className={`h-1.5 w-6 rounded-full ${index < step ? "bg-emerald-500" : index === step ? "bg-brand-600" : "bg-brand-200"}`}
            />
          ))}
        </div>
      </div>
      <p className="line-clamp-2 text-xs text-slate-600">{STARTERS[step]}</p>
      <button
        className="mt-2 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
        onClick={() => onRun(STARTERS[step], step)}
        disabled={loading}
      >
        {loading ? "Waiting for Qwen..." : `Run step ${step + 1}`}
      </button>
    </div>
  );
}

function ActionSummary({ actions }: { actions: ChatResponse["memory_actions"] }) {
  const parts: string[] = [];
  if (actions.created.length) parts.push(`+${actions.created.length} created`);
  if (actions.superseded.length) parts.push(`${actions.superseded.length} superseded`);
  if (actions.updated.length) parts.push(`~${actions.updated.length} merged`);
  if (actions.forgotten.length) parts.push(`${actions.forgotten.length} forgotten`);
  if (actions.redacted.length) parts.push("secret redacted");
  if (parts.length === 0) return null;
  return <div className="mt-1 text-[11px] text-slate-400">{parts.join(" / ")}</div>;
}
