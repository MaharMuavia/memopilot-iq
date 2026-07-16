"""Ablation study for the MemoryOS governance mechanisms.

Quantifies the contribution of each design choice by disabling one mechanism at
a time and measuring retrieval/assembly quality. Everything is computed at the
memory-layer stage (no LLM answer generation), so the study is deterministic and
exactly reproducible offline, and it isolates the memory layer from the model.

Variants:
  * Full (proposed)        - the complete scoring + critical guarantee + lifecycle exclusion.
  * - critical guarantee   - critical/pinned compete by score instead of being force-included.
  * - lifecycle exclusion  - superseded/expired records are eligible and their penalties removed.
  * similarity only        - rank by semantic similarity alone (weights zeroed elsewhere).
  * uniform weights        - equal positive weights, no penalties (untuned policy).

Metrics (per variant, aggregated over scenarios):
  * context recall         - target memory present in the assembled context.
  * leak rate              - a genuinely outdated memory injected (lower is better).
  * critical inclusion     - critical memory injected when it fits the strict budget.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from ..memory import MemoryOS
from ..memory.embeddings import cosine_similarity
from ..memory.retriever import _keyword_overlap
from ..memory.scorer import WEIGHTS, score_memory
from ..memory.trace import approx_tokens
from ..models import MemoryStatus
from .benchmark import _has_leak, _keywords_present, load_scenarios

_EXCLUDED = {
    MemoryStatus.superseded, MemoryStatus.expired,
    MemoryStatus.deleted, MemoryStatus.archived,
}
_POSITIVE = [
    "semantic_similarity", "importance", "recency_score", "confidence",
    "usage_score", "project_match", "critical_bonus",
]
TOP_K = 8
BUDGET = 2500


def _full() -> Dict[str, float]:
    return dict(WEIGHTS)


def _no_penalties() -> Dict[str, float]:
    w = dict(WEIGHTS)
    w["outdated_penalty"] = w["privacy_penalty"] = w["superseded_penalty"] = 0.0
    return w


def _sim_only() -> Dict[str, float]:
    w = {k: 0.0 for k in WEIGHTS}
    w["semantic_similarity"] = 1.0
    return w


def _uniform() -> Dict[str, float]:
    w = {k: 0.0 for k in WEIGHTS}
    for k in _POSITIVE:
        w[k] = 1.0 / len(_POSITIVE)
    return w


# (name, weights, critical_guarantee, include_excluded, budget, top_k)
VARIANTS = [
    ("Full (proposed)", _full(), True, False, BUDGET, TOP_K),
    ("$-$ lifecycle exclusion", _no_penalties(), True, True, BUDGET, TOP_K),
    ("similarity only", _sim_only(), False, False, BUDGET, TOP_K),
    ("uniform weights", _uniform(), True, False, BUDGET, TOP_K),
]


def _final(components: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(weights[k] * components[k] for k in WEIGHTS)


class AblationRunner:
    def __init__(self, memos: MemoryOS) -> None:
        self.memos = memos

    async def run(self) -> Dict[str, Any]:
        scenarios = load_scenarios()["scenarios"]
        user = f"abl-{uuid.uuid4().hex[:8]}"

        tallies = {
            name: {"recall_hit": 0, "recall_tot": 0, "leak": 0, "leak_tot": 0,
                   "crit_hit": 0, "crit_tot": 0}
            for name, *_ in VARIANTS
        }

        for sc in scenarios:
            project = f"abl-{sc['id']}"
            for msg in sc["setup_messages"]:
                await self.memos.remember(user_id=user, project_id=project,
                                          session_id="abl", message=msg)
            # expire temporary memories so the lifecycle case is exercised
            await self._age_temporary(user, project)
            await self.memos.forgetting.sweep(user, project)

            q_emb = await self.memos.qwen.embed(sc["test_question"])
            mems_all = await self.memos.store.list(user, project, include_all=True)
            expected = sc["expected_answer_keywords"]
            forbidden = sc["must_not_use_keywords"]

            # precompute hybrid similarity + score components for every record
            scored = []
            for m in mems_all:
                dense = cosine_similarity(q_emb, m.embedding)
                sparse = _keyword_overlap(sc["test_question"], m)
                sim = max(dense, 0.5 * dense + 0.5 * sparse)
                comp = score_memory(m, sim, project)
                scored.append((m, comp))

            has_expected = bool(expected)
            crit_mem_ids = [m.memory_id for m, _ in scored if m.is_critical]

            for name, weights, guarantee, include_excluded, budget, top_k in VARIANTS:
                injected = self._assemble(scored, weights, guarantee, include_excluded, budget, top_k)
                inj_dicts = [{"memory": {"content": m.content, "memory_id": m.memory_id}}
                             for m in injected]
                inj_text = " ".join(m.content for m in injected)

                t = tallies[name]
                if has_expected:
                    t["recall_tot"] += 1
                    if _keywords_present(inj_text, expected):
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
        for name, *_ in VARIANTS:
            t = tallies[name]
            results.append({
                "variant": name,
                "recall_at_5": round(t["recall_hit"] / t["recall_tot"], 2) if t["recall_tot"] else None,
                "leak_rate": round(t["leak"] / t["leak_tot"], 2) if t["leak_tot"] else None,
                "critical_inclusion": round(t["crit_hit"] / t["crit_tot"], 2) if t["crit_tot"] else None,
            })
        return {"variants": results, "num_scenarios": len(scenarios)}

    def _assemble(self, scored, weights, guarantee, include_excluded, budget, top_k):
        """Greedy budget assembly under a variant, returning injected records."""
        cands = []
        for m, comp in scored:
            if not include_excluded and m.status in _EXCLUDED:
                continue
            cands.append((m, _final(comp, weights)))

        def is_priority(m):
            return guarantee and (m.is_critical or m.status == MemoryStatus.pinned)

        cands.sort(key=lambda x: (is_priority(x[0]), x[1]), reverse=True)

        injected, tokens, count = [], 0, 0
        for m, _ in cands:
            cost = approx_tokens(m.content)
            if is_priority(m) and tokens + cost <= budget:
                injected.append(m)
                tokens += cost
                count += 1
            elif count < top_k and tokens + cost <= budget:
                injected.append(m)
                tokens += cost
                count += 1
        return injected

    async def _age_temporary(self, user_id, project_id):
        from datetime import datetime, timedelta, timezone
        from ..models import MemoryType
        for m in await self.memos.store.list(user_id, project_id, include_all=True):
            if m.type == MemoryType.temporary:
                m.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
                await self.memos.store.update(m)
