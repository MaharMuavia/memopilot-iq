# LoCoMo Benchmark Harness

[LoCoMo](https://github.com/snap-research/locomo) (Maharana et al., ACL 2024)
is the standard long-conversation memory benchmark used by Mem0, Zep, and
A-Mem: 10 very-long multi-session dialogues (~19 sessions, ~590 turns each)
with ~1,540 non-adversarial QA pairs across multi-hop, temporal, open-domain,
and single-hop categories. MemoPilot IQ ships a full adapter so it can be
evaluated head-to-head with published systems on this shared protocol.

## Run it

```bash
cd backend
python scripts/run_locomo.py --download          # fetch official dataset (git-ignored)
python scripts/run_locomo.py --retrieval-only    # deterministic memory-layer eval
python scripts/run_locomo.py --max-conversations 3 --max-qa 50   # answer-level (live Qwen)
```

## Protocol

- **Ingestion:** `verbatim` mode stores one memory per dialogue turn (speaker +
  session date + text + image caption), tagged with its `dia_id`; `extract`
  mode runs the full Memory Editor pipeline instead.
- **Answering:** standard MemoryOS retrieve → score → budget assembly
  (top-k 8, 2,500-token budget), then a short-phrase answer from the LLM.
- **Grading:** SQuAD-style normalized token-F1 and exact match, per category.
  Category 5 (adversarial) is skipped by default, matching Mem0's public
  protocol.
- **Evidence recall (model-independent):** the fraction of questions for which
  at least one annotated evidence turn was actually injected into the context.
  This isolates the *memory layer* from the answer model and runs offline.

## Archived exploratory results

The tables below are from an earlier exploratory run and are retained only as
an example of the harness output. They are **not final submission evidence**:
the current build's evaluator and context-budget behavior have changed. Rerun
the commands above with the final deployed configuration, preserve the raw
JSON/checkpoints, and replace this section before publishing or comparing with
other systems.

### Answer level (live run: `qwen3.7-max` + `text-embedding-v3`)

3 conversations (conv-26/30/44), 1,451 turns ingested verbatim, 150 QA,
top-k 8 within the 2,500-token budget, strict token-F1/EM grading:

| Category | n | F1 | EM | Evidence recall@8 |
|---|---|---|---|---|
| temporal | 67 | 0.308 | 0.164 | 0.403 |
| open-domain | 13 | 0.331 | 0.077 | 0.364 |
| multi-hop | 57 | 0.189 | 0.018 | 0.333 |
| single-hop | 13 | 0.158 | 0.077 | 0.231 |
| **overall** | **150** | **0.252** | **0.093** | **0.358** |

### The decomposition that matters

Conditioning F1 on whether the annotated evidence turn made it into the
assembled context:

| | n | F1 | EM |
|---|---|---|---|
| Evidence **retrieved** into context | 53 | **0.572** | 0.245 |
| Evidence **missed** | 95 | 0.068 | 0.011 |

An **8.4× F1 uplift** when the memory layer delivers the evidence. The
answering side works; the binding constraint at this configuration is
retrieval depth — k=8 memories from ~480 candidate turns under a tight token
budget. That is a *tunable dial* (raise `--top-k`/budget, or swap in stronger
embeddings), not a flaw in the governance mechanism, and the harness makes the
trade-off directly measurable.

### Retrieval level (model-independent)

| Setting | Conversations | QA | Evidence recall@8 |
|---|---|---|---|
| Offline hash embeddings (deterministic) | 10 (full) | 1,540 | 0.23 |
| Live `text-embedding-v3` | 3 | 150 | **0.36** |

Random evidence recall at k=8 over ~480–600 turns is ≈0.02, so the layer is
~12–18× above chance.

### Comparability caveats (read before quoting)

These are deliberately conservative first-cut numbers: strict token-F1 (no
LLM-as-judge), short-phrase prompting, verbatim per-turn ingestion (no
summarization advantage), and a k=8 / 2,500-token budget. Published Mem0/Zep
LoCoMo results use **LLM-judged** grading and deeper retrieval, so absolute
values are **not directly comparable**. The honest head-to-head this harness
enables is running each system with the *same answer model and grader*;
checkpoint/resume (`--checkpoint`, on by default) makes long runs
interruption-safe.

## Notes

- The dataset is **not redistributed** in this repo (`backend/data/` is
  git-ignored); the `--download` flag fetches it from the official repository.
- Verbatim turn-memories are a deliberately conservative substrate: no
  summarization, no extraction advantage — the layer competes on retrieval and
  budgeting alone. `--mode extract` tests the full extraction pipeline instead.
