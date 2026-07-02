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

## Preliminary results (retrieval level)

| Setting | Conversations | QA | Evidence recall@8 |
|---|---|---|---|
| Offline hash embeddings (deterministic) | 10 (full) | 1,540 | 0.23 |
| Live `text-embedding-v3` | 1 (conv-26) | 60 | **0.33** (temporal 0.39, open-domain 0.43) |

Context: each question retrieves from ~420–600 verbatim turn-memories, so
random evidence recall at k=8 is ≈0.02 — the memory layer is ~12–17× above
chance, and real embeddings clearly beat the hash fallback. These are
**retrieval-level** numbers with a tight k=8 / 2,500-token budget; published
Mem0/Zep LoCoMo results are **answer-level** (LLM-judged/F1) with different
retrieval depths, so absolute values are not directly comparable. The honest
head-to-head requires the full answer-level run (same answer model for all
systems), which this harness supports (`--max-conversations`/`--max-qa` to
control cost).

## Notes

- The dataset is **not redistributed** in this repo (`backend/data/` is
  git-ignored); the `--download` flag fetches it from the official repository.
- Verbatim turn-memories are a deliberately conservative substrate: no
  summarization, no extraction advantage — the layer competes on retrieval and
  budgeting alone. `--mode extract` tests the full extraction pipeline instead.
