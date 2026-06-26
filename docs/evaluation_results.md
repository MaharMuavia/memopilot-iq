# Evaluation Results — Live Qwen Run

**Backend:** Alibaba Cloud DashScope (OpenAI-compatible endpoint)
**Chat model:** `qwen3.7-max` · **Embeddings:** `text-embedding-v3`
**Mode:** `LOCAL_MODE` (SQLite + Qwen embeddings) · **Context budget:** 2,500 tokens
**Reproduce:** `POST /api/eval/run` (run `uvicorn app.main:app` with a real `QWEN_API_KEY`).

## Benchmark — memory agent vs. no-memory baseline

| Metric | Memory agent | No-memory baseline |
|---|---|---|
| Task accuracy | **1.00** | 0.33 |
| Accuracy delta | **+0.67** | — |
| Recall@5 | **1.00** | — |
| Outdated-memory errors | **0** | — |
| Outdated-memory avoidance | **1.00** | — |
| Preference adherence | **1.00** | — |
| Token savings vs. full history | **≈ 97%** | — |
| Avg. retrieval latency | **8.9 ms** | — |

### Per-scenario

| Scenario | Memory agent | Baseline |
|---|---|---|
| Preference recall | ✅ | ❌ |
| Cross-session project decision recall | ✅ | ❌ |
| Contradiction / supersession | ✅ | ❌ |
| Expired deadline avoidance | ✅ | ✅ |
| Critical memory recall | ✅ | ✅ |
| No-memory vs memory comparison | ✅ | ❌ |

The two scenarios the baseline solves are the ones answerable without state; the
four it fails require persistent memory (cross-session recall, supersession),
which a stateless model cannot have.

## Judge demo (`POST /api/demo/run`, live Qwen)

| Session | Created | Superseded | Recalled | Tokens used |
|---|---|---|---|---|
| 1 — states preferences | 7 | 0 | 0 | 0 / 2500 |
| 2 — "Design the backend architecture" | 0 | 0 | 7 | 44 / 2500 |
| 3 — "Use Next.js instead of React + Vite" | 1 | **1** | 7 | 44 / 2500 |
| 4 — "What stack should I use now?" | 0 | 0 | 7 | 52 / 2500 |

**Final state:** Next.js active; **React + Vite superseded and never re-injected**;
critical "Never commit API keys" remained active throughout.

## Reflection pass (`POST /api/reflect`, live Qwen)

- Reviewed 7 active memories → promoted 5 (raised importance from usage) →
  derived 1 insight: *"You have 5 active preference memories guiding this project."*

## Memory graph (`GET /api/graph`)

- 9 nodes, 6 edges, including **1 supersession edge** (React + Vite → Next.js).

> Numbers above are a single live run on six diagnostic scenarios; the offline
> deterministic backend reproduces the same qualitative behavior without
> credentials. See `backend/app/eval/` for the harness and scenarios.
