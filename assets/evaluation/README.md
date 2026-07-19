# Final evaluation evidence

These artifacts were generated on **2026-07-19** by the public Alibaba Cloud
deployment at build [`97b1ff57f36c`](https://github.com/MaharMuavia/memopilot-iq/commit/97b1ff57f36c).
They contain synthetic benchmark data only—no credentials or user data.

| Artifact | Purpose |
|---|---|
| [`final-qwen-eval-2026-07-19-97b1ff57f36c.json`](final-qwen-eval-2026-07-19-97b1ff57f36c.json) | Raw 24-scenario Qwen answer evaluation, including answers, grading reasons, provider status, token usage, and deployed SHA |
| [`final-ablation-2026-07-19-97b1ff57f36c.json`](final-ablation-2026-07-19-97b1ff57f36c.json) | Raw five-strategy memory-layer ablation with lifecycle, recall, token, and latency metrics |
| [`benchmark-summary.svg`](benchmark-summary.svg) | Judge-facing vector summary generated from the two raw artifacts |

## Verified result

| Metric | Result |
|---|---:|
| Qwen provider status | `online` |
| Provider fallbacks | `0` |
| Governed-memory answer accuracy | **24/24 (100%)** |
| No-memory answer accuracy | 38% |
| Raw full-history answer accuracy | 83% |
| Model-generated history-summary accuracy | 92% |
| Recall in admitted context | **22/22 (100%)** |
| Outdated-memory errors | **0** |
| Historical-context token reduction | **21%** |
| Average retrieval latency | **7.3 ms** |

This is a diagnostic suite, not a claim of general benchmark superiority. The
answer evaluator uses declared expected concepts, declared aliases,
alphanumeric term boundaries, and rejection-aware stale-option checks. The
ablation uses the same extracted scenario memories for all strategies and makes
zero final-answer model calls.
