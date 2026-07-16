# Demo Video Script (under 3 minutes)

> Seed first so the store is demo-ready: `cd backend && SEED_DEMO=1 uvicorn app.main:app --port 8000`
> (Windows PowerShell: `$env:SEED_DEMO=1; uvicorn app.main:app --port 8000`).
> Or just run the four Chat starter buttons live in order.

| Time | On screen | Narration |
|---|---|---|
| 0:00–0:15 | App header, mode badge | "AI assistants forget everything between sessions. MemoPilot IQ is a persistent-memory agent — it remembers, forgets, and explains what matters." |
| 0:15–0:35 | Chat tab, send starter #1 | "I tell it my preferences: FastAPI, React + Vite, Alibaba Cloud, light UI, never commit API keys. Watch the memory badges — it created structured memories and tagged the API-key rule as **critical**." |
| 0:35–1:05 | Send "Design the backend architecture." + Trace panel | "Next session I ask for an architecture. The **Memory Trace** shows exactly which memories were retrieved, their scores, and that critical constraints are prioritized within a strict 2,500-token budget." |
| 1:05–1:35 | Send starter #3 (Next.js) | "I change my mind: use Next.js instead of React + Vite. The agent **supersedes** the old memory — see the ↻ badge and the Timeline event." |
| 1:35–2:05 | Send starter #4 + Trace | "Now I ask what stack to use. It recommends Next.js and the Trace shows the old React + Vite memory marked **superseded and ignored** — no outdated advice." |
| 2:05–2:30 | Evaluation tab → Run benchmark | "The Evaluation Dashboard runs a 24-scenario diagnostic against a no-memory baseline. It reports the final build's strict evaluator, context recall, stale-memory checks, historical-context token reduction, and latency." |
| 2:30–2:50 | /health + deployment doc / consoles | "Everything runs on Qwen Cloud for chat, extraction and embeddings, with Alibaba Cloud Tablestore + OSS for persistence — health endpoint confirms the mode." |
| 2:50–3:00 | Header | "MemoPilot IQ — a memory layer any AI assistant can plug into. Thanks for watching." |

## Talking points if asked
- Secrets are redacted before storage (try pasting a fake `sk-...` key).
- Forgetting is non-destructive: superseded/expired memories stay on the
  timeline but never enter the context.
- Works fully offline (deterministic fallback) so the demo never depends on
  network/credentials.
