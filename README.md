# MemoPilot IQ

[![Track](https://img.shields.io/badge/Qwen%20Cloud-Track%201%3A%20MemoryAgent-4f46e5?style=for-the-badge)](SUBMISSION.md)
[![Alibaba Cloud](https://img.shields.io/badge/Deployed%20on-Alibaba%20Cloud%20ECS-ff6a00?style=for-the-badge)](docs/alibaba_cloud_proof.md)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-HTTPS-2563eb?style=for-the-badge)](https://47-84-129-218.sslip.io/app)
[![Video Demo](https://img.shields.io/badge/Video%20Demo-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/UE2h4K_VaL8)
[![Build Journey](https://img.shields.io/badge/Build%20Journey-Dev.to-0a0a0a?style=for-the-badge)](https://dev.to/muhammad_muavia/ai-agents-dont-need-more-memory-they-need-memory-governance-15ej)
[![Backend tests](https://img.shields.io/badge/Backend%20tests-101%20passing-22c55e?style=for-the-badge)](docs/submission_readiness.md)
[![Qwen evaluation](https://img.shields.io/badge/Qwen%20evaluation-24%2F24-16a34a?style=for-the-badge)](docs/evaluation_results.md)

> **A self-curating persistent-memory agent that remembers, forgets, and explains what matters.**

**Qwen Cloud Global AI Hackathon — Track 1: MemoryAgent**

> **Naming disclosure:** MemoPilot IQ is an independent Qwen Cloud hackathon
> project and is not affiliated with the separate 2026 research system named
> MemoPilot described in [arXiv:2606.08656](https://arxiv.org/abs/2606.08656).

MemoPilot IQ is a persistent-memory AI agent. Unlike a normal chatbot that only
sees recent chat history, it has a dedicated **MemoPilot memory-governance
layer** that extracts structured memories from conversations, stores them
persistently, retrieves only the most relevant ones inside a strict token
budget, updates and supersedes outdated memories, expires temporary ones, and
shows a transparent **Memory Trace** explaining why each memory was used,
ignored, updated, or forgotten.

> ### [Launch the live MemoPilot IQ deployment →](https://47-84-129-218.sslip.io/app)
> Running publicly on **Alibaba Cloud ECS** in `ALIBABA_CLOUD_MODE`; no account
> or credentials are required. [View deployment proof](docs/alibaba_cloud_proof.md)
> [Watch the public demo video](https://youtu.be/UE2h4K_VaL8)
> · [Read the Qwen Cloud build journey](https://dev.to/muhammad_muavia/ai-agents-dont-need-more-memory-they-need-memory-governance-15ej)

---

## Table of contents
1. [Executive summary](#executive-summary)
2. [Problem statement](#problem-statement)
3. [Key features](#key-features)
4. [Architecture](#architecture)
5. [How Qwen Cloud API is used](#how-qwen-cloud-api-is-used)
6. [How Alibaba Cloud is used](#how-alibaba-cloud-is-used)
7. [Memory-governance algorithm](#memory-governance-algorithm)
8. [Forgetting engine](#forgetting-engine)
9. [Setup & local run](#setup--local-run)
10. [Environment variables](#environment-variables)
11. [Alibaba deployment](#alibaba-deployment)
12. [API docs](#api-docs)
13. [Testing](#testing)
14. [Demo script](#demo-script)
15. [Evaluation results](#evaluation-results)
16. [Judging criteria mapping](#judging-criteria-mapping)
17. [Screenshots](#screenshots)
18. [License](#license)

Submission release gate: [docs/submission_readiness.md](docs/submission_readiness.md).
Submission package: [SUBMISSION.md](SUBMISSION.md) · [editable presentation deck](assets/memopilot-iq-hackathon-deck.pptx) · [Alibaba deployment handoff](docs/alibaba_deployment_handoff.md).

---

## Executive summary
MemoPilot IQ autonomously accumulates experience across conversations. It
remembers user preferences, project decisions, mistakes, goals, constraints and
deadlines, and makes increasingly accurate decisions across multi-turn and
cross-session interactions. It demonstrates sophisticated use of **Qwen Cloud**
APIs, an **Alibaba Cloud** persistence/deployment adapter, a custom memory scoring engine,
selective forgetting, a clean modular architecture, an evaluation benchmark, and
a transparent UI.

The submitted build runs in **ALIBABA_CLOUD_MODE**: Alibaba Cloud ECS hosts the
Docker deployment, Qwen Cloud powers chat/extraction/embeddings, Alibaba
Tablestore persists memories and events, and Alibaba OSS receives redacted turn
snapshots. The live mode is visible in the UI header and on `GET /health`.

## Problem statement
AI assistants forget everything between sessions. Developers and students
re-explain their stack, decisions and constraints repeatedly, and assistants
keep giving **outdated advice** after a decision changes (e.g. switching
frameworks). MemoPilot IQ fixes this with a persistent, self-curating memory
layer that knows what to remember, what to forget, and can prove its reasoning.

## Key features
> **Implementation note:** Memory priority never overrides the configured token
> budget; memory consolidation is deterministic and does not train model
> weights; the diagnostic suite has 24 scenarios; and Alibaba deployment is
> considered complete only after a live deployment has been evidenced.

- 🧠 **Structured memory extraction** (12 types) via a Qwen "Memory Editor" — not raw chat logs.
- 🎯 **Custom scoring formula** blending semantics, importance, recency, usage, project match, criticality and penalties.
- 🔎 **Hybrid retrieval** — dense embeddings + sparse keyword/tag overlap + structured filters.
- 📏 **Context budget manager** — strict 2,500-token budget; critical/pinned memories are prioritized.
- ♻️ **Forgetting engine** — expire deadlines, archive stale memories, supersede contradicted decisions (non-destructive).
- 🪞 **Memory Trace** — see exactly which memories were injected/skipped, their scores, reasons and token cost.
- 📊 **Evaluation dashboard** — a 24-scenario answer diagnostic plus comparative memory-layer baselines (full history, dense-only, recency-only, lifecycle-disabled, and full governance).
- 🧹 **Memory consolidation** — a deterministic pass that merges duplicates, promotes frequently-used memories, and creates source-linked cluster summaries.
- 🕸️ **Live Memory Graph** — interactive visualization of memories with supersession/related edges, critical rings, and consolidation-summary nodes.
- 📈 **Analytics dashboard** — memory growth, type/status distribution, forgetting rate, token savings.
- 🔒 **Secret-safe** — secrets are redacted before storage; never committed.
- ☁️ **Alibaba Cloud deployment** — ECS compute, Qwen Cloud, Tablestore, and OSS.
- ✅ **CI + Docker** — GitHub Actions (tests + build) and one-command `docker compose up`.
- 🏭 **Production platform** — optional API-key auth, per-key rate limiting,
  Prometheus `/metrics`, paginated + filtered memory API, per-memory audit
  history, and a two-stage rerank that bounds expensive hybrid scoring after
  tenant-scoped candidates are loaded.
- 🐍 **Python SDK** — embed the MemoPilot memory layer in any agent in a few lines
  ([sdk/python](sdk/python/README.md)).
- 🔬 **LoCoMo harness** — evaluate on the standard long-conversation memory
  benchmark used by Mem0/Zep, with F1/EM grading and a model-independent
  evidence-recall metric ([docs/locomo.md](docs/locomo.md)).

## Architecture
See [docs/architecture.md](docs/architecture.md) for the full Mermaid diagram and
request lifecycle. Rendered diagram: [assets/architecture.svg](assets/architecture.svg)
(Mermaid source: [assets/architecture.mmd](assets/architecture.mmd)).

![Architecture](assets/architecture.svg)

```
User → React + Vite frontend → FastAPI backend → MemoPilot memory layer
   MemoPilot memory layer → Qwen Cloud chat API
   MemoPilot memory layer → Qwen embedding API
   MemoPilot memory layer → Alibaba Tablestore (persistent memories + events)
   MemoPilot memory layer → Alibaba OSS (redacted snapshots / eval reports)
   MemoPilot memory layer → Context Builder → Qwen Cloud → Response + Trace
```

## How Qwen Cloud API is used
All AI calls go through [`backend/app/qwen_client.py`](backend/app/qwen_client.py)
against the DashScope OpenAI-compatible endpoint:
- **Chat / reasoning** — `qwen-plus` (configurable) generates the final answer
  from the budgeted memory context.
- **Memory extraction** — JSON-only "Memory Editor" prompt returns structured
  `new_memories`, `updates`, and `forget` actions.
- **Embeddings** — `text-embedding-v3` powers semantic retrieval.

If `QWEN_API_KEY` is unset, a deterministic offline implementation keeps the
whole app, tests and benchmark working end-to-end.

## How Alibaba Cloud is used
- **Tablestore** — persistent memory + event store with tenant/project/record
  composite keys and tenant-scoped range reads
  ([`store_alibaba.py`](backend/app/memory/store_alibaba.py)).
- **OSS** — redacted turn snapshots and evaluation artifacts ([`oss_client.py`](backend/app/storage/oss_client.py)).
- **Submitted deployment** — Nginx and FastAPI Docker containers on Alibaba Cloud ECS.
Full guide & proof checklist: [docs/deployment_alibaba.md](docs/deployment_alibaba.md).
See the [live deployment proof gallery](docs/alibaba_cloud_proof.md) and the
[published Qwen Cloud build journey](https://dev.to/muhammad_muavia/ai-agents-dont-need-more-memory-they-need-memory-governance-15ej).

## Memory-governance algorithm
Full detail (scoring weights, retrieval, extraction, states/types) in
[docs/memory_algorithm.md](docs/memory_algorithm.md). The scoring formula:

```
final_score = 0.40*semantic + 0.20*importance + 0.15*recency + 0.10*confidence
            + 0.10*usage + 0.15*project_match + 0.20*critical_bonus
            - 0.30*outdated - 0.25*privacy - 0.50*superseded
```

## Forgetting engine
Expires deadlines/temporary memories, archives unused low-importance memories
after 30 days, and supersedes contradicted decisions. Nothing is silently
hard-deleted — superseded/expired memories remain on the timeline but are never
injected into context. Users can Pin, Archive, Forget, Export, and Forget-all.

## Setup & local run

**Prerequisites:** Python 3.11+ and Node 18+.

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 (proxies /api to :8000)
```

The frontend uses **React Router**:
- `/` — professional product landing page (hero, problem/solution, features,
  architecture flow, demo scenario, evaluation preview, hackathon compliance).
- `/app` — the MemoryAgent dashboard (Chat, Memory Trace, **Graph**, Timeline,
  **Analytics**, Evaluation, Controls, Settings), with a one-click **Judge
  Demo**. Reached via **Launch App**, with a **← Home** link back to the
  landing page.
- `/demo` — alias that redirects to `/app`.

### One command (both, from repo root)
```bash
npm install          # installs concurrently
npm run dev          # starts backend + frontend together
```

### Docker (full stack, one command)
```bash
docker compose up --build    # backend :8000 + frontend :5173
```
CI runs the backend tests and frontend build on every push — see
[.github/workflows/ci.yml](.github/workflows/ci.yml).

### Seed the scripted demo
```bash
# macOS/Linux:
cd backend && SEED_DEMO=1 uvicorn app.main:app --port 8000
# Windows PowerShell:
cd backend; $env:SEED_DEMO=1; uvicorn app.main:app --port 8000
```

No Qwen or Alibaba credentials are required for isolated local development;
the app has a deterministic offline fallback for development and tests. The
submitted deployment uses the Alibaba Cloud services shown above.

## Environment variables
Copy [`.env.example`](.env.example) to `backend/.env` and fill in real values
(placeholders only in the example; `.env` is git-ignored).

| Variable | Purpose |
|---|---|
| `APP_MODE` | Use `alibaba` for the submitted cloud deployment |
| `QWEN_API_KEY` / `QWEN_BASE_URL` | Qwen Cloud auth + endpoint |
| `QWEN_CHAT_MODEL` / `QWEN_EMBEDDING_MODEL` | Qwen models |
| `QWEN_REQUEST_TIMEOUT_SECONDS` / `QWEN_MAX_RETRIES` | Bounded provider timeout and transient retry policy |
| `QWEN_ENABLE_THINKING` / `QWEN_MAX_OUTPUT_TOKENS` | Qwen reasoning mode and response-size ceiling |
| `ALIBABA_ACCESS_KEY_ID/SECRET/REGION` | Alibaba Cloud credentials |
| `ALIBABA_OSS_BUCKET/ENDPOINT` | OSS storage |
| `ALIBABA_TABLESTORE_ENDPOINT/INSTANCE` | Tablestore memory store |
| `MEMORY_STORE` | Use `alibaba` for the submitted cloud deployment |
| `DATABASE_URL` | Optional development database path |
| `EVAL_REPORT_PATH` | Optional persistent path for the latest synthetic evaluation report |
| `FRONTEND_ORIGIN` | Frontend CORS origin, comma-separated origins, or `*` for a public demo |
| `MEMORY_TOKEN_BUDGET` / `RETRIEVAL_TOP_K` | Context budget and retrieval depth |
| `RETRIEVAL_MIN_SIMILARITY` | Semantic admission threshold; default `0.62` |
| `RETRIEVAL_MIN_KEYWORD_OVERLAP` | Lexical admission threshold; default `0.20` |
| `EVAL_MAX_CONCURRENCY` | Concurrent model calls during evaluation (default 4, maximum 8) |
| `MEMOPILOT_API_KEYS` / `RATE_LIMIT_PER_MINUTE` | Optional API auth and rate limit |
| `MEMOPILOT_PUBLIC_DEMO_ISOLATION` / `MEMOPILOT_IDENTITY_SECRET` | Signed HttpOnly anonymous-tenant isolation for a public browser demo |
| `MEMOPILOT_ADMIN_KEY` | Protect expensive evaluation POST endpoints with `X-Admin-Key` |
| `APP_BUILD_SHA` | Deployed revision exposed by `/health` and Settings |

## Alibaba deployment
See [docs/deployment_alibaba.md](docs/deployment_alibaba.md) for ECS (Docker),
Function Compute (`serverless.yaml`) and ACK instructions, plus the proof
checklist (health screenshot, Tablestore rows, OSS objects).

## API docs
Interactive OpenAPI docs at `http://localhost:8000/docs`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Status, mode, Qwen/store configuration |
| POST | `/api/chat` | Memory-augmented chat; returns answer + used memories + actions + trace + mode |
| GET | `/api/memories` | List memories by user/project |
| POST | `/api/memories` | Create a memory manually |
| PATCH | `/api/memories/{id}` | Pin / archive / edit / change status |
| DELETE | `/api/memories/{id}` | Delete (soft by default, `?hard=true` to remove) |
| GET | `/api/memories/timeline` | Memory event timeline |
| GET | `/api/memories/export` | Export memories as JSON |
| POST | `/api/memories/forget-all` | Clear all memories for a project |
| POST | `/api/memory/extract` | Run extraction manually |
| GET | `/api/memories/{id}/history` | Per-memory audit trail (all lifecycle events) |
| GET | `/metrics` | Prometheus metrics (requests, latency, 401/429 counters) |
| POST | `/api/eval/run` | Run the benchmark |
| POST | `/api/eval/ablation` | Run the governance ablation study |
| GET | `/api/eval/report` | Latest evaluation report |
| POST | `/api/demo/run` | Run the optional deterministic 4-session lifecycle check |
| GET | `/api/trace/{session_id}` | Latest Memory Trace for a session |
| POST | `/api/reflect` | Run deterministic memory consolidation |
| GET | `/api/analytics` | Aggregate memory analytics |
| GET | `/api/graph` | Memory graph nodes + edges |

**Production hardening** (all optional, zero-friction locally): set
`MEMOPILOT_API_KEYS=key1,key2` to require an `X-API-Key` header on `/api/*`,
and `RATE_LIMIT_PER_MINUTE` (default 120) for per-key/IP rate limiting.
For a browser-accessible public demo, enable signed anonymous isolation with
`MEMOPILOT_PUBLIC_DEMO_ISOLATION=true` and a persistent random
`MEMOPILOT_IDENTITY_SECRET`. Configure `MEMOPILOT_ADMIN_KEY` to prevent public
execution of expensive evaluation jobs.
`GET /api/memories` supports `type`, `status`, `q` (text search), `limit`,
`offset`. See [sdk/python](sdk/python/README.md) for the embeddable client.

## Testing
```bash
cd backend
python -m pytest
```
Frontend type-check / build:
```bash
cd frontend && npm run build
```

Current release verification: **101 backend tests pass** and the production
frontend build completes successfully.

## Demo script
The under-3-minute walkthrough is in [docs/demo_script.md](docs/demo_script.md).
The Chat tab has four starter buttons that replay the 4-session demo.

## Evaluation results
The final Qwen-backed evaluation was generated by deployed build
`97b1ff57f36c` with Qwen online and zero fallbacks. MemoPilot's governed context
answered **24/24 scenarios**, recalled **22/22** required memories, produced
**zero stale-memory errors**, and used **21% fewer historical-context tokens**
than raw full history. The realistic baselines scored 38% (no memory), 83% (raw
history), and 92% (LLM history summary).

[![Final Qwen evaluation](assets/evaluation/benchmark-summary.svg)](docs/evaluation_results.md)

See the [methodology and full results](docs/evaluation_results.md), the
[raw Qwen report](assets/evaluation/final-qwen-eval-2026-07-19-97b1ff57f36c.json),
and the [raw ablation report](assets/evaluation/final-ablation-2026-07-19-97b1ff57f36c.json).

## Judging criteria mapping
See [docs/judging_mapping.md](docs/judging_mapping.md) for the full rubric and
rule-compliance checklist.

## Screenshots
These captures come from the [live Alibaba Cloud deployment](https://47-84-129-218.sslip.io/app).
Select any image to open the full-resolution proof. The complete evidence trail
is documented in [docs/alibaba_cloud_proof.md](docs/alibaba_cloud_proof.md).

### Alibaba Tablestore retrieval

[![Alibaba Tablestore memory retrieval](assets/proof/01-cloud-memory-retrieval.png)](assets/proof/01-cloud-memory-retrieval.png)

### Automatic memory creation

[![Automatic memory creation](assets/proof/02-automatic-memory-creation.png)](assets/proof/02-automatic-memory-creation.png)

### Cross-session recall

[![Cross-session recall](assets/proof/03-cross-session-recall.png)](assets/proof/03-cross-session-recall.png)

The final public video will demonstrate the same flow in under three minutes.

## License
[MIT](LICENSE).
