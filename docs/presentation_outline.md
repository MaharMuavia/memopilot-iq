# Presentation / PPT Outline — MemoPilot IQ

**Track 1: MemoryAgent · Qwen Cloud Global AI Hackathon**

### Slide 1 — Title
MemoPilot IQ — *A self-improving persistent-memory agent that remembers,
forgets, and explains what matters.* Team / logo / track.

### Slide 2 — Problem
AI assistants forget everything between sessions. Developers and students
re-explain preferences, decisions and constraints constantly; assistants give
outdated advice after a decision changes.

### Slide 3 — Solution
A dedicated **memory intelligence layer (MemoryOS)** on top of Qwen Cloud:
extract → classify → score → retrieve → budget → forget → explain.

### Slide 4 — Architecture
Diagram: User → React frontend → FastAPI → MemoryOS → Qwen Cloud (chat +
embeddings) + Alibaba Tablestore + OSS. (Use `assets/architecture.png`.)

### Slide 5 — MemoryOS pipeline
12 memory types, 6 states. Extraction redacts secrets, detects contradictions,
sets expiries, merges duplicates. Timeline event for every change.

### Slide 6 — Retrieval & scoring
The weighted scoring formula; hybrid dense+sparse retrieval; critical/pinned
always first; superseded/expired never injected.

### Slide 7 — Forgetting engine
Expire deadlines, archive stale low-value memories, supersede contradicted
decisions — non-destructive, fully explained in the UI.

### Slide 8 — Demo scenario
5-session script: create preferences → recall in architecture answer →
supersede React+Vite with Next.js → outdated memory ignored.

### Slide 9 — Evaluation results
Memory agent ~0.9 vs baseline ~0.45 accuracy; recall@5 high; 0 outdated errors;
~60% token savings; ~tens-of-ms retrieval. Live dashboard.

### Slide 10 — Qwen + Alibaba Cloud proof
Qwen for chat/extraction/embeddings; Tablestore + OSS persistence; deployed on
ECS/Function Compute. `/health` shows the active mode.

### Slide 11 — Impact & roadmap
Drop-in memory layer for any assistant. Roadmap: multi-user auth, team memory
sharing, FAISS/Chroma at scale, memory analytics, RAG over documents.
