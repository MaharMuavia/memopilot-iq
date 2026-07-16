# Evaluation Protocol and Reporting

MemoPilot IQ includes a **24-scenario diagnostic suite** covering preference
recall, cross-session recall, supersession, temporary-memory expiry, critical
constraints, and multi-fact composition. Run it with `POST /api/eval/run` or
the Evaluation dashboard.

## What the report measures

- Strict keyword accuracy for the memory-augmented answer and a no-memory
  baseline. An answer containing a forbidden/outdated term is not counted as a
  pass, even if it also contains an expected term.
- Recall in the assembled context at the configured retrieval depth.
- Stale-memory leaks in the assembled context.
- Historical-context token reduction, comparing selected memory text against
  the complete seeded history. Shared system and current-message tokens are
  excluded from both sides.
- Retrieval latency, model label, evaluator version, scenario count, and
  retrieval depth.

## Reproducibility rules

1. Run the benchmark against the exact model used in the submission demo.
2. Save the returned JSON report under `assets/evaluation/` with the date,
   model, and commit SHA in the filename.
3. If comparing models, run the same suite and prompt version for each model;
   report all runs, not only the best one.
4. Treat this as a diagnostic benchmark, not a claim of general long-context
   superiority. LoCoMo results, if included, must retain their dataset,
   command, model, and scoring configuration.

## Before submission

Replace this protocol-only document with a concise table generated from the
final deployed build. Include the raw JSON artifact, environment-free command,
model name, retrieval depth, evaluator version, date, and any failure/skip
counts. Do not reuse numbers produced by a different model, prompt, benchmark
version, or deployment.
