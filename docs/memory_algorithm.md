# MemoryOS Algorithm

MemoryOS is the custom memory operating layer. It has nine cooperating
components plus user controls.

## 1. Memory types & states

**Types:** `preference`, `project`, `decision`, `mistake`, `constraint`,
`deadline`, `learning_goal`, `task`, `critical`, `temporary`, `outdated`,
`deleted_by_user`.

**States:** `active`, `pinned`, `archived`, `expired`, `superseded`, `deleted`.

Only `active`/`pinned` memories are ever injected into the model context.
`superseded`/`expired`/`deleted`/`archived` are retained for the timeline and
history inspection but excluded from retrieval.

## 2. Scoring formula (`memory/scorer.py`)

```
final_score =
    0.40 * semantic_similarity
  + 0.20 * importance
  + 0.15 * recency_score
  + 0.10 * confidence
  + 0.10 * usage_score
  + 0.15 * project_match
  + 0.20 * critical_bonus
  - 0.30 * outdated_penalty
  - 0.25 * privacy_penalty
  - 0.50 * superseded_penalty
```

- `semantic_similarity` — cosine(query, memory) in `[0,1]`.
- `recency_score` — exponential decay, 14-day half-life.
- `usage_score` — diminishing returns on `usage_count`.
- `project_match` — 1.0 when the memory belongs to the active project.
- `critical_bonus` — 1.0 for critical/pinned memories.
- penalties push outdated, private/sensitive, and superseded memories down.

Critical/pinned memories are additionally sorted **first**, before score, so
they are always considered for inclusion.

## 3. Hybrid retrieval (`memory/retriever.py`)

`similarity = max(dense, 0.5*dense + 0.5*keyword_overlap)` — dense vector
search blended with sparse tag/keyword overlap, after structured filtering by
`user_id` + `project_id` and exclusion of non-active states.

## 4. Context budget manager (`memory/context_builder.py`)

Token budget defaults to **2,500**. Inclusion order: critical/pinned first
within the strict budget → top-k semantic → drop the rest. The system prompt and the
current user message are always present and not counted against the memory
budget. Every decision is recorded in the trace.

## 5. Extraction pipeline (`memory/extractor.py`)

1. Redact secrets before extraction.
2. Qwen "Memory Editor" returns strict JSON (`new_memories`, `updates`, `forget`).
3. Drop anything still secret-like.
4. Merge near-duplicates (`SequenceMatcher > 0.86`) instead of duplicating.
5. Detect topic-level contradictions (framework, cloud, theme…) and supersede
   the old memory (never supersedes critical memories).
6. Set `expires_at` for temporary/deadline memories.
7. Embed and persist; emit a timeline event.

## 6. Forgetting engine (`memory/forgetting.py`)

- Expire deadlines/temporary memories once `expires_at` passes.
- Archive unused (`usage_count == 0`), low-importance (`< 0.35`) memories after
  30 days.
- Never hard-deletes silently — only the user (DELETE endpoint / "Forget"
  button) can hard-delete. Critical memories are never auto-archived.

## 7. Trace explainer (`memory/trace.py`)

For every answer the trace exposes: included vs skipped memories, each one's
final score and component breakdown, the human-readable reason, approximate
token cost, candidates considered, and retrieval latency.

## 8. Reflection / consolidation (`memory/reflection.py`)

A consolidation "sleep" pass the agent can run over its active memory set:

- **Merge** near-duplicate memories of the same type (`SequenceMatcher ≥ 0.82`);
  the strongest survives, the rest are archived (non-destructive) and the
  survivor's importance/usage are boosted.
- **Promote** frequently-used memories (`usage_count ≥ 2`) by raising importance.
- **Derive insights** from clusters: a type with ≥ 3 active memories produces a
  higher-level insight memory (tagged `insight`), shown as a gold ★ node in the
  Memory Graph. Insight creation is idempotent.

Exposed via `POST /api/reflect` and the Analytics tab. Feeds the Memory Graph
(`GET /api/graph`) and Analytics (`GET /api/analytics`) views.

## 9. Evaluation runner (`eval/benchmark.py`)

Runs `eval/scenarios.json` for both the memory agent and a no-memory baseline
and aggregates strict-keyword accuracy, recall in the assembled context,
outdated-avoidance, historical-context token reduction, and
latency. See [judging_mapping.md](judging_mapping.md).
