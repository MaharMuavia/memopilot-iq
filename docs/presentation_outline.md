# Presentation Outline — MemoPilot IQ

**Track 1: MemoryAgent · Qwen Cloud Global AI Hackathon**

### Slide 1 — Title

MemoPilot IQ — a persistent-memory layer that remembers, retires stale facts,
and explains its choices.

### Slide 2 — Problem

Conversation history is not durable memory: it grows without governance and
can replay decisions that a user later changed.

### Slide 3 — Solution

The MemoPilot memory-governance layer extracts typed records, scores and retrieves them, assembles a strict
context budget, applies lifecycle rules, and exposes a Memory Trace.

### Slide 4 — Architecture

User → React + Vite → FastAPI on Alibaba Cloud ECS → MemoPilot memory layer →
Qwen Cloud (chat, extraction, embeddings). Show `assets/architecture.svg` with
Alibaba Tablestore for persistent memories and Alibaba OSS for redacted
snapshots and evaluation artifacts.

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

Show Qwen usage in the live chat/extraction path, the Alibaba Cloud badges, and
the cross-session recall proof. Use `assets/proof/03-cross-session-recall.png`
to show the retrieved Tablestore memory and its Memory Trace score.

### Slide 11 — Limits and roadmap

The live demo is intentionally scoped to a hackathon deployment. A production
service still needs TLS, real identity management, key rotation, and
distributed rate limiting. Next: publish the demo video and attach the final
model-backed evaluation report.
