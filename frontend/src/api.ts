// Typed API client for the MemoPilot IQ backend.
// In dev, Vite proxies /api and /health to the FastAPI server (see vite.config.ts).

const BASE = import.meta.env.VITE_API_BASE || "";

export type MemoryType =
  | "preference" | "project" | "decision" | "mistake" | "constraint"
  | "deadline" | "learning_goal" | "task" | "critical" | "temporary"
  | "outdated" | "deleted_by_user";

export type MemoryStatus =
  | "active" | "pinned" | "archived" | "expired" | "superseded" | "deleted";

export interface MemoryRecord {
  memory_id: string;
  user_id: string;
  project_id: string | null;
  session_id: string;
  type: MemoryType;
  status: MemoryStatus;
  content: string;
  summary: string;
  importance: number;
  confidence: number;
  recency_score: number;
  usage_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  supersedes: string | null;
  superseded_by: string | null;
  is_critical: boolean;
  privacy_level: "public" | "private" | "sensitive";
  reason: string;
}

export interface ScoredMemory {
  memory: MemoryRecord;
  score: number;
  components: Record<string, number>;
  included: boolean;
  reason: string;
  approx_tokens: number;
}

export interface MemoryTrace {
  included: ScoredMemory[];
  skipped: ScoredMemory[];
  token_budget: number;
  tokens_used: number;
  candidates_considered: number;
  retrieval_latency_ms: number;
  notes: string[];
}

export interface MemoryActions {
  created: { memory_id: string; type?: string; content?: string }[];
  updated: { memory_id: string; action?: string }[];
  superseded: { memory_id: string; superseded_by?: string }[];
  forgotten: { memory_id: string; action?: string }[];
  redacted: string[];
}

export interface ChatResponse {
  answer: string;
  used_memories: MemoryRecord[];
  memory_actions: MemoryActions;
  trace: MemoryTrace;
  mode: string;
  qwen_provider_status: "online" | "offline" | "degraded_offline_fallback";
  qwen_fallback_used: boolean;
}

export interface HealthInfo {
  status: string;
  service: string;
  mode: string;
  qwen_configured: boolean;
  qwen_provider_status: "online" | "offline" | "degraded_offline_fallback";
  qwen_model: string;
  memory_store: string;
  alibaba_configured: boolean;
  oss_configured: boolean;
  token_budget: number;
  tenant_isolation: string;
  storage_schema: string;
  build_sha: string;
}

export interface TimelineEvent {
  kind: string;
  memory_id: string;
  type: string;
  content: string;
  reason: string;
  timestamp: string;
  project_id?: string | null;
}

export interface EvalReport {
  generated_at: string;
  build_sha: string;
  duration_seconds: number;
  primary_backbone: string;
  provider_status: string;
  provider_fallbacks: number;
  memory_agent_accuracy: number;
  baseline_no_memory_accuracy: number;
  baseline_full_history_accuracy: number;
  baseline_history_summary_accuracy: number;
  memory_recall_at_context: number;
  outdated_memory_errors: number;
  outdated_memory_avoidance: number;
  preference_adherence: number;
  token_savings_percent: number;
  response_accuracy_delta: number;
  retrieval_top_k: number;
  memory_token_budget: number;
  chat_model: string;
  embedding_model: string;
  evaluator: string;
  provider_token_usage: {
    operations: Record<string, Record<string, number>>;
    totals: Record<string, number>;
  };
  avg_retrieval_latency_ms: number;
  retrieval_latency_ms: number;
  scenarios: {
    id: string;
    title: string;
    memory_agent_correct: boolean;
    baseline_correct: boolean;
    full_history_correct: boolean;
    history_summary_correct: boolean;
    agent_answer: string;
    answer_failure_reason?: string | null;
    context_recall: boolean;
    tokens_used: number;
    forbidden_leaked: boolean;
  }[];
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    // Network-level failure: backend not reachable.
    throw new Error(
      "Cannot reach the backend. Start it with `uvicorn app.main:app --port 8000` in backend/, then retry."
    );
  }
  if (!res.ok) {
    // Prefer the structured JSON error the backend returns.
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
      if (body?.request_id) detail += ` (ref: ${body.request_id})`;
    } catch {
      /* non-JSON body; keep the generic message */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

function getOrCreateDemoUser(): string {
  const storageKey = "memopilot-demo-user-v1";
  try {
    const existing = window.localStorage.getItem(storageKey);
    if (existing) return existing;
    const random = new Uint32Array(3);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(random);
    } else {
      random.set([
        Math.floor(Math.random() * 0xffffffff),
        Date.now() >>> 0,
        Math.floor(Math.random() * 0xffffffff),
      ]);
    }
    const suffix = Array.from(random, (value) => value.toString(16).padStart(8, "0")).join("");
    const userId = `demo-${suffix}`;
    window.localStorage.setItem(storageKey, userId);
    return userId;
  } catch {
    return `demo-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }
}

export const DEFAULT_USER = getOrCreateDemoUser();
export const DEFAULT_PROJECT = "qwen-memoryagent";

export const api = {
  health: () => req<HealthInfo>("/health"),
  chat: (message: string, sessionId: string) =>
    req<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        user_id: DEFAULT_USER,
        project_id: DEFAULT_PROJECT,
        session_id: sessionId,
        message,
      }),
    }),
  listMemories: (includeAll = true) =>
    req<{ memories: MemoryRecord[]; count: number }>(
      `/api/memories?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}&include_all=${includeAll}`
    ),
  timeline: () =>
    req<{ events: TimelineEvent[]; count: number }>(
      `/api/memories/timeline?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`
    ),
  pin: (id: string) =>
    req<MemoryRecord>(`/api/memories/${id}?user_id=${DEFAULT_USER}`, {
      method: "PATCH",
      body: JSON.stringify({ pin: true }),
    }),
  archive: (id: string) =>
    req<MemoryRecord>(`/api/memories/${id}?user_id=${DEFAULT_USER}`, {
      method: "PATCH",
      body: JSON.stringify({ archive: true }),
    }),
  remove: (id: string) =>
    req<{ deleted: string }>(`/api/memories/${id}?user_id=${DEFAULT_USER}`, { method: "DELETE" }),
  forgetAll: () =>
    req<{ forgotten: number }>(
      `/api/memories/forget-all?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`,
      { method: "POST" }
    ),
  exportMemories: () =>
    req<unknown>(
      `/api/memories/export?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`
    ),
  runEval: () => req<EvalReport>("/api/eval/run", { method: "POST" }),
  getEvalReport: () => req<EvalReport>("/api/eval/report"),
  runDemo: () => req<DemoResult>("/api/demo/run", { method: "POST" }),
  getTrace: (sessionId: string) => req<unknown>(`/api/trace/${sessionId}`),
  reflect: () =>
    req<ReflectionReport>(
      `/api/reflect?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`,
      { method: "POST" }
    ),
  analytics: () =>
    req<AnalyticsReport>(
      `/api/analytics?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`
    ),
  graph: () =>
    req<GraphData>(
      `/api/graph?user_id=${DEFAULT_USER}&project_id=${DEFAULT_PROJECT}`
    ),
};

export interface ReflectionReport {
  reviewed: number;
  merged: { memory_id: string; into: string }[];
  promoted: { memory_id: string; from: number; to: number }[];
  summaries: { memory_id: string; summary: string; source_memory_ids: string[] }[];
  ran_at: string;
}

export interface AnalyticsReport {
  totals: {
    total: number;
    active: number;
    superseded: number;
    expired: number;
    archived: number;
    critical: number;
  };
  type_counts: Record<string, number>;
  status_counts: Record<string, number>;
  event_kind_counts: Record<string, number>;
  growth: { date: string; count: number; cumulative: number }[];
  token_savings_percent: number | null;
  total_events: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  status: string;
  is_critical: boolean;
  importance: number;
  is_consolidation_summary: boolean;
  tags: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: "supersedes" | "related";
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DemoTurn {
  session_id: string;
  message: string;
  expectation: string;
  answer: string;
  injected_memories: { content: string; type: string; is_critical: boolean }[];
  actions: {
    created: number;
    superseded: number;
    forgotten: number;
    redacted: number;
    superseded_ids: { memory_id: string; superseded_by?: string }[];
  };
  trace: {
    tokens_used: number;
    token_budget: number;
    included: number;
    skipped: number;
    retrieval_latency_ms: number;
  };
}

export interface DemoResult {
  user_id: string;
  project_id: string;
  turns: DemoTurn[];
  final_state: { active: string[]; superseded: string[] };
}
