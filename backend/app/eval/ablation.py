"""Ablation study for the MemoPilot memory-governance mechanisms.

Quantifies the contribution of each design choice by disabling one mechanism at
a time and measuring retrieval/assembly quality. Everything is computed at the
memory-layer stage (no LLM answer generation), so the study is deterministic and
exactly reproducible offline, and it isolates the memory layer from the model.

Baselines and variants:
  * Full conversation history - raw setup turns, without retrieval/governance.
  * Dense-only retrieval      - cosine ranker with lifecycle exclusion.
  * Recency-only retrieval    - latest records with lifecycle exclusion.
  * Hybrid without lifecycle  - hybrid score while allowing inactive records.
  * Full governance           - production scoring, priority and lifecycle policy.

Metrics (per variant, aggregated over scenarios):
  * context recall         - target memory present in the assembled context.
  * leak rate              - a genuinely outdated memory injected (lower is better).
  * critical inclusion     - critical memory injected when it fits the strict budget.
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from ..memory import MemoryOS
from ..memory.embeddings import cosine_similarity
from ..memory.retriever import _keyword_overlap
from ..memory.scorer import WEIGHTS, score_memory
from ..memory.trace import approx_tokens, memory_context_text
from ..models import MemoryRecord, MemoryStatus
from .benchmark import _has_leak, _keywords_present, load_scenarios

_EXCLUDED = {
    MemoryStatus.superseded, MemoryStatus.expired,
    MemoryStatus.deleted, MemoryStatus.archived,
}
TOP_K = 8
BUDGET = 2500


def _full() -> dict[str, float]:
    return dict(WEIGHTS)


def _sim_only() -> dict[str, float]:
    w = {k: 0.0 for k in WEIGHTS}
    w["semantic_similarity"] = 1.0
    return w


def _recency_only() -> dict[str, float]:
    weights = {key: 0.0 for key in WEIGHTS}
    weights["recency_score"] = 1.0
    return weights


# (name, weights, priority_ordering, include_excluded, budget, top_k)
VARIANTS: list[tuple[str, dict[str, float], bool, bool, int, int]] = [
    ("Full governance", _full(), True, False, BUDGET, TOP_K),
    ("Dense-only retrieval", _sim_only(), False, False, BUDGET, TOP_K),
    ("Recency-only retrieval", _recency_only(), False, False, BUDGET, TOP_K),
    ("Hybrid without lifecycle exclusion", _full(), True, True, BUDGET, TOP_K),
]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return round(ordered[index], 3)


def _final(components: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights[k] * components[k] for k in WEIGHTS)


class AblationRunner:
    def __init__(self, memos: MemoryOS) -> None:
        self.memos = memos

    async def run(self) -> dict[str, Any]:
        scenarios = load_scenarios()["scenarios"]
        user = f"abl-{uuid.uuid4().hex[:8]}"

        tallies = {
            name: {"recall_hit": 0, "recall_tot": 0, "leak": 0, "leak_tot": 0,
                   "crit_hit": 0, "crit_tot": 0, "tokens": 0, "latencies": []}
            for name, *_ in VARIANTS
        }
        tallies["Full conversation history"] = {
            "recall_hit": 0, "recall_tot": 0, "leak": 0, "leak_tot": 0,
            "crit_hit": 0, "crit_tot": 0, "tokens": 0, "latencies": [],
        }

        for sc in scenarios:
            project = f"abl-{sc['id']}"
            for msg in sc["setup_messages"]:
                await self.memos.remember(user_id=user, project_id=project,
                                          session_id="abl", message=msg)
            # Time advances only in scenarios that explicitly test expiry.
            if sc.get("expire_temporary_before_test", False):
                await self._age_temporary(user, project)
            await self.memos.forgetting.sweep(user, project)

            q_emb = await self.memos.qwen.embed(sc["test_question"])
            mems_all = await self.memos.store.list(user, project, include_all=True)
            expected = sc["expected_answer_keywords"]
            expected_alternatives = sc.get("expected_answer_alternatives", {})
            forbidden = sc["must_not_use_keywords"]

            # Raw-history baseline: no retrieval and no lifecycle filtering.
            history = " ".join(sc["setup_messages"])
            history_tally = tallies["Full conversation history"]
            if expected:
                history_tally["recall_tot"] += 1
                history_tally["recall_hit"] += int(
                    _keywords_present(history, expected, expected_alternatives)
                )
            history_tally["leak_tot"] += 1
            history_tally["leak"] += int(
                _has_leak(
                    [{"memory": {"content": message}} for message in sc["setup_messages"]],
                    expected,
                    forbidden,
                )
            )
            history_tally["tokens"] += approx_tokens(history)

            # Precompute dense, sparse, hybrid, and governance components.
            scored = []
            for m in mems_all:
                dense = cosine_similarity(q_emb, m.embedding)
                sparse = _keyword_overlap(sc["test_question"], m)
                sim = max(dense, 0.5 * dense + 0.5 * sparse)
                comp = score_memory(m, sim, project)
                comp["dense_similarity"] = dense
                comp["keyword_overlap"] = sparse
                scored.append((m, comp))

            has_expected = bool(expected)
            crit_mem_ids = [m.memory_id for m, _ in scored if m.is_critical]

            for name, weights, priority, include_excluded, budget, top_k in VARIANTS:
                variant_scored = scored
                if name == "Dense-only retrieval":
                    variant_scored = [
                        (memory, {**components, "semantic_similarity": components["dense_similarity"]})
                        for memory, components in scored
                    ]
                started = time.perf_counter()
                if name == "Full governance":
                    production_candidates = [
                        (memory, components)
                        for memory, components in variant_scored
                        if memory.status not in _EXCLUDED
                    ]
                    _, _, injected = self.memos.context_builder.build(
                        sc["test_question"],
                        production_candidates,
                        project,
                        candidates_considered=len(production_candidates),
                        retrieval_latency_ms=0.0,
                    )
                else:
                    injected = self._assemble(
                        variant_scored, weights, priority, include_excluded, budget, top_k
                    )
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                inj_dicts = [{"memory": {"content": memory_context_text(m), "memory_id": m.memory_id}}
                             for m in injected]
                inj_text = " ".join(memory_context_text(m) for m in injected)

                t = tallies[name]
                t["latencies"].append(elapsed_ms)
                t["tokens"] += sum(
                    approx_tokens(memory_context_text(memory)) for memory in injected
                )
                if has_expected:
                    t["recall_tot"] += 1
                    if _keywords_present(inj_text, expected, expected_alternatives):
                        t["recall_hit"] += 1
                t["leak_tot"] += 1
                if _has_leak(inj_dicts, expected, forbidden):
                    t["leak"] += 1
                if crit_mem_ids:
                    t["crit_tot"] += 1
                    if any(m.memory_id in crit_mem_ids for m in injected):
                        t["crit_hit"] += 1

        await self.memos.store.clear_user(user, None)

        results = []
        result_order = ["Full conversation history", *[name for name, *_ in VARIANTS]]
        for name in result_order:
            t = tallies[name]
            leak_rate = round(t["leak"] / t["leak_tot"], 2) if t["leak_tot"] else None
            results.append({
                "variant": name,
                "context_recall": round(t["recall_hit"] / t["recall_tot"], 2) if t["recall_tot"] else None,
                "stale_memory_leak_rate": leak_rate,
                "lifecycle_safety": round(1.0 - leak_rate, 2) if leak_rate is not None else None,
                "critical_inclusion": round(t["crit_hit"] / t["crit_tot"], 2) if t["crit_tot"] else None,
                "avg_context_tokens": round(t["tokens"] / len(scenarios), 1),
                "retrieval_latency_p50_ms": _percentile(t["latencies"], 0.50),
                "retrieval_latency_p95_ms": _percentile(t["latencies"], 0.95),
            })
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "build_sha": os.getenv("APP_BUILD_SHA", "development"),
            "evaluator": "deterministic-memory-layer-ablation-v3",
            "variants": results,
            "num_scenarios": len(scenarios),
            "retrieval_top_k": TOP_K,
            "memory_token_budget": BUDGET,
            "qwen_answer_calls": 0,
            "notes": [
                "This ablation evaluates memory assembly, not final-answer quality.",
                "Latency measures in-process assembly after embeddings are available.",
            ],
        }

    def _assemble(
        self,
        scored: list[tuple[MemoryRecord, dict[str, float]]],
        weights: dict[str, float],
        priority_ordering: bool,
        include_excluded: bool,
        budget: int,
        top_k: int,
    ) -> list[MemoryRecord]:
        """Greedy budget assembly under a variant, returning injected records."""
        cands = []
        for m, comp in scored:
            if not include_excluded and m.status in _EXCLUDED:
                continue
            cands.append((m, _final(comp, weights)))

        def is_priority(m: MemoryRecord) -> bool:
            return priority_ordering and (
                m.is_critical or m.status == MemoryStatus.pinned
            )

        cands.sort(key=lambda x: (is_priority(x[0]), x[1]), reverse=True)

        injected, tokens, count = [], 0, 0
        for m, _ in cands:
            cost = approx_tokens(memory_context_text(m))
            if is_priority(m) and tokens + cost <= budget:
                injected.append(m)
                tokens += cost
                count += 1
            elif count < top_k and tokens + cost <= budget:
                injected.append(m)
                tokens += cost
                count += 1
        return injected

    async def _age_temporary(self, user_id: str, project_id: str) -> None:
        from datetime import datetime, timedelta, timezone
        from ..models import MemoryType
        for m in await self.memos.store.list(user_id, project_id, include_all=True):
            if m.type == MemoryType.temporary:
                m.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
                await self.memos.store.update(m)
