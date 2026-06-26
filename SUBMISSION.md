# MemoPilot IQ — Submission Package

**Qwen Cloud Global AI Hackathon · Track 1: MemoryAgent**

This page maps every submission requirement to its artifact in this repository.

| # | Requirement | Status | Link |
|---|---|---|---|
| 1 | Public code repository | ✅ | https://github.com/MaharMuavia/memopilot-iq |
| 2 | Open-source LICENSE (detectable in About) | ✅ MIT | [LICENSE](LICENSE) |
| 3 | All source + setup/test instructions | ✅ | [README.md](README.md) |
| 4 | Alibaba Cloud proof (code file) | ✅ | see [§ Alibaba Cloud Proof](#alibaba-cloud-proof) |
| 5 | Architecture diagram | ✅ | [assets/architecture.png](assets/architecture.png) · [docs/architecture.md](docs/architecture.md) |
| 6 | Text description of features | ✅ | see [§ Project Description](#project-description) |
| 7 | Track identification | ✅ | **Track 1: MemoryAgent** |
| 8 | ~3 min demo video (public) | ⏳ you record | script: [docs/demo_script.md](docs/demo_script.md) |
| 9 | Alibaba deployment proof recording | ⏳ you record | guide: [docs/deployment_alibaba.md](docs/deployment_alibaba.md) |
| 10 | (Optional) Blog / social post | ⏳ you publish | draft: [docs/blog_post.md](docs/blog_post.md) |

---

## Project Description

**MemoPilot IQ** is a **MemoryOS platform** for AI agents — not a chatbot with
chat history. It autonomously extracts structured memories from conversation,
scores them with a transparent formula, retrieves only the most relevant ones
inside a strict token budget, forgets/supersedes outdated information, and
explains every memory decision via a per-answer **Memory Trace**.

**Key features:** persistent + cross-session memory, hybrid retrieval, context
budget manager, intelligent forgetting, contradiction/supersession, critical
memory pinning, a self-improving **Reflection** pass, a **Live Memory Graph**,
an **Analytics** dashboard, an **Evaluation** benchmark vs. a no-memory
baseline, and secret-safe storage. Dual runtime: `LOCAL_MODE` (SQLite + local
vectors, runs with no keys) and `ALIBABA_CLOUD_MODE` (Tablestore + OSS).

**Verified live results (`qwen3.7-max`):** memory-agent accuracy **1.00** vs.
baseline **0.33**, recall@5 **1.00**, **0** outdated-memory leaks, **97%** token
savings, **8.9 ms** retrieval latency — see
[docs/evaluation_results.md](docs/evaluation_results.md).

---

## Alibaba Cloud Proof

MemoPilot IQ uses Alibaba Cloud in three concrete ways. **All AI runs on
Alibaba Cloud's Qwen (DashScope) API — this is live and proven by the
evaluation results above.**

**Primary proof file (live Alibaba Cloud API calls):**
👉 [`backend/app/qwen_client.py`](backend/app/qwen_client.py) — chat, JSON
memory-extraction, and embeddings against the Alibaba Cloud **DashScope**
endpoint (`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`).

**Persistent storage adapters (Alibaba Cloud services & APIs):**
- [`backend/app/memory/store_alibaba.py`](backend/app/memory/store_alibaba.py) — Alibaba Cloud **Tablestore** (OTS) memory store.
- [`backend/app/storage/oss_client.py`](backend/app/storage/oss_client.py) — Alibaba Cloud **OSS** for logs / snapshots / eval reports.

**Deployment target & instructions:**
- [`backend/Dockerfile`](backend/Dockerfile) + [`backend/serverless.yaml`](backend/serverless.yaml) — ECS / Function Compute / ACK.
- [`docs/deployment_alibaba.md`](docs/deployment_alibaba.md) — full deploy + proof-recording guide.

> For the **deployment recording**, deploy the Docker image to an Alibaba Cloud
> ECS instance (or Function Compute) and screen-record `GET /health` returning
> `"mode":"ALIBABA_CLOUD_MODE"` from the public ECS IP, plus the Tablestore/OSS
> consoles showing data. Steps are in `docs/deployment_alibaba.md`.

---

## How to run (for judges)

```bash
# Backend
cd backend && python -m venv .venv && .venv\Scripts\activate   # (or source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && npm install && npm run dev      # http://localhost:5173
# Or full stack: docker compose up --build
```

Runs with **no credentials** (offline Qwen fallback). Add `QWEN_API_KEY` to
`backend/.env` for live Qwen. Tests: `cd backend && python -m pytest` (40 tests).
