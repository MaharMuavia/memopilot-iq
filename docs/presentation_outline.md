# Presentation Outline — MemoPilot IQ

**Track 1: MemoryAgent · Qwen Cloud Global AI Hackathon**

### Slide 1 — Title

MemoPilot IQ — a persistent-memory layer that remembers, retires stale facts,
and explains its choices.

### Slide 2 — Problem

Conversation history is not durable memory: it grows without governance and
can replay decisions that a user later changed.

### Slide 3 — Solution

MemoryOS extracts typed records, scores and retrieves them, assembles a strict
context budget, applies lifecycle rules, and exposes a Memory Trace.

### Slide 4 — Architecture

User → React → FastAPI → MemoryOS → Qwen (chat, extraction, embeddings).
Show `assets/architecture.png`; local mode uses SQLite, cloud mode targets
Tablestore and OSS.

### Slide 5 — Memory lifecycle

Demonstrate active, pinned, superseded, expired, archived, and deleted states.
Show a changed technical decision replacing a prior one.

### Slide 6 — Retrieval and safety

Show hybrid retrieval, the interpretable scoring factors, the strict budget,
secret-safe persistence, and the trace for included and skipped memories.

### Slide 7 — User control

Show edit, pin, archive, hard delete, export, and **Forget all**. Explain that
Forget all removes the selected project's memories and prior timeline events.

### Slide 8 — Live demo

Run the documented multi-session scenario: save a preference, ask a follow-up,
change a decision, then show the old decision being excluded.

### Slide 9 — Evaluation

Run the 24-scenario diagnostic on the build being shown. Display its generated
report — strict answer checks, context recall, stale-memory checks,
historical-context reduction, and latency. Do not display preset figures.

### Slide 10 — Qwen and Alibaba Cloud proof

Show Qwen usage in the live chat/extraction path. After deployment, show the
actual Alibaba-mode `/health` response plus Tablestore and OSS console evidence.
Until then, describe the Alibaba implementation as deployment-ready code, not
as a completed cloud deployment.

### Slide 11 — Limits and roadmap

Local demo mode is open; an Internet-facing service requires TLS, real identity
management, key rotation, and distributed rate limiting. Next: complete the
Alibaba deployment, attach evidence, and rerun final model-backed evaluation.
