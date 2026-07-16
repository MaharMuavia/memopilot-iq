# Judging Criteria Mapping

| Criterion | Weight | How MemoPilot IQ addresses it | Evidence |
|---|---|---|---|
| **Innovation & AI Creativity** | 30% | Qwen Cloud powers chat, structured memory extraction, and embeddings. Custom **MemoryOS** scoring formula, selective forgetting, contradiction/supersession, and a transparent Memory Trace. | `memory/scorer.py`, `memory/extractor.py`, `MemoryTracePanel.tsx` |
| **Technical Depth** | 30% | Modular FastAPI; hybrid (dense+sparse) retrieval; strict context budget manager; evaluation benchmark; local/cloud adapters; error handling; and a backend test suite. | `memory/`, `eval/benchmark.py`, `tests/` |
| **Problem Value** | 25% | Solves AI assistants forgetting project context across sessions. Useful to developers, students and teams. Productizable as a drop-in memory layer for any assistant. | README problem statement, demo |
| **Presentation** | 15% | Clean light glassmorphism UI, architecture diagram, <3-min demo script, complete README, evaluation dashboard, memory timeline, PPT outline. | `docs/`, `frontend/` |

## Hackathon rule compliance

- ✅ Track 1: MemoryAgent
- ✅ Uses Qwen Cloud API (chat, extraction, embeddings)
- ⏳ Alibaba Cloud deployment evidence — capture after the final ECS/FC deployment
- ✅ Public/open-source, **MIT** `LICENSE`
- ✅ README install + testing instructions
- ✅ `.env.example` with empty placeholders only; `.env` git-ignored
- ✅ Architecture diagram (Qwen, backend, DB, memory engine, frontend)
- ✅ Feature/functionality description (README + docs)
- ✅ Demo script kept under 3 minutes
- ✅ Presentation/PPT outline
- ✅ English throughout
- ✅ Original implementation; OSS libs used only as building blocks
- ✅ Local demo and tests run without cloud credentials via a deterministic fallback
