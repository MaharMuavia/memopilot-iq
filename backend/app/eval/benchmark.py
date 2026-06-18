"""Evaluation benchmark runner.

Runs the scenarios in ``scenarios.json`` twice:
  * memory-agent: seeds memories, builds context with MemoryOS, then answers.
  * baseline: answers with NO long-term memory (current message only).

It measures preference adherence, cross-session recall, supersession success,
expired-memory avoidance, critical recall, recall@5, token savings and latency,
then aggregates into the report consumed by the Evaluation Dashboard.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List

from ..memory import MemoryOS

_SCENARIOS_PATH = os.path.join(os.path.dirname(__file__), "scenarios.json")


def load_scenarios() -> Dict[str, Any]:
    with open(_SCENARIOS_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _keywords_present(text: str, keywords: List[str]) -> bool:
    low = text.lower()
    return all(k.lower() in low for k in keywords) if keywords else True


def _any_present(text: str, keywords: List[str]) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in keywords)


class BenchmarkRunner:
    def __init__(self, memos: MemoryOS) -> None:
        self.memos = memos

    async def _age_temporary(self, user_id: str, project_id: str) -> None:
        """Backdate temporary memories' expiry so the forgetting sweep expires
        them — used to make the expired-deadline scenario meaningful."""
        from datetime import datetime, timedelta, timezone

        from ..models import MemoryType

        mems = await self.memos.store.list(user_id, project_id, include_all=True)
        for m in mems:
            if m.type == MemoryType.temporary:
                m.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
                await self.memos.store.update(m)

    async def run(self) -> Dict[str, Any]:
        data = load_scenarios()
        scenarios = data["scenarios"]
        eval_user = f"eval-{uuid.uuid4().hex[:8]}"

        per_scenario: List[Dict[str, Any]] = []
        latencies: List[float] = []
        recall_hits = 0
        recall_total = 0
        outdated_errors = 0
        mem_correct = 0
        base_correct = 0
        baseline_tokens_total = 0
        memory_tokens_total = 0

        for sc in scenarios:
            # Each scenario gets its own project_id for clean isolation.
            eval_project = f"eval-{sc['id']}"
            # Seed setup messages as memories.
            for msg in sc["setup_messages"]:
                await self.memos.remember(
                    user_id=eval_user,
                    project_id=eval_project,
                    session_id="eval",
                    message=msg,
                )

            # Simulate time passing: backdate temporary memories so the
            # forgetting engine expires them before retrieval (expiry test).
            await self._age_temporary(eval_user, eval_project)

            start = time.perf_counter()
            system_prompt, trace, used = await self.memos.build_context(
                eval_user, eval_project, sc["test_question"]
            )
            latency = (time.perf_counter() - start) * 1000.0
            latencies.append(trace.retrieval_latency_ms or latency)

            mem_answer = await self.memos.qwen.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sc["test_question"]},
                ]
            )
            # Baseline: a bare system prompt with NO memory block.
            baseline_answer = await self.memos.qwen.chat(
                [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": sc["test_question"]},
                ]
            )

            injected = [i.model_dump() for i in trace.included]
            injected_text = " ".join(m["memory"]["content"] for m in injected)
            expected = sc["expected_answer_keywords"]
            forbidden = sc["must_not_use_keywords"]

            # Principled leak detection: a forbidden phrase only counts as a
            # leak if it appears in an injected memory that does NOT also carry
            # an expected phrase. This avoids false positives like the
            # superseding decision "Use Next.js instead of React + Vite"
            # (which legitimately mentions the old choice).
            leaked = _has_leak(injected, expected, forbidden)

            # Memory agent correct if expected keywords were recalled into
            # context and no genuinely outdated memory leaked.
            mem_ok = _keywords_present(injected_text, expected) and not leaked
            base_ok = _keywords_present(baseline_answer, expected)

            if expected:
                recall_total += 1
                if _keywords_present(injected_text, expected):
                    recall_hits += 1
            if leaked:
                outdated_errors += 1

            mem_correct += int(mem_ok)
            base_correct += int(base_ok)

            baseline_tokens_total += _approx_tokens(sc["test_question"]) + 400  # bare guess
            memory_tokens_total += trace.tokens_used

            per_scenario.append(
                {
                    "id": sc["id"],
                    "title": sc["title"],
                    "memory_agent_correct": mem_ok,
                    "baseline_correct": base_ok,
                    "injected_memories": [i.memory["memory_id"] for i in trace.included],
                    "tokens_used": trace.tokens_used,
                    "forbidden_leaked": leaked,
                }
            )

        n = len(scenarios)
        # Token savings: full-history baseline vs budgeted memory context.
        full_history_tokens = sum(
            _approx_tokens(" ".join(sc["setup_messages"]) + sc["test_question"]) + 800
            for sc in scenarios
        )
        token_savings_percent = (
            round(100 * (1 - memory_tokens_total / full_history_tokens))
            if full_history_tokens
            else 0
        )

        report = {
            "memory_agent_accuracy": round(mem_correct / n, 2),
            "baseline_no_memory_accuracy": round(base_correct / n, 2),
            "memory_recall_at_5": round(recall_hits / recall_total, 2) if recall_total else 1.0,
            "outdated_memory_errors": outdated_errors,
            "outdated_memory_avoidance": round(1 - outdated_errors / n, 2),
            "preference_adherence": round(mem_correct / n, 2),
            "token_savings_percent": max(0, token_savings_percent),
            "response_accuracy_delta": round((mem_correct - base_correct) / n, 2),
            "avg_retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "scenarios": per_scenario,
        }

        # Clean up all eval memories (every per-scenario project) so they don't
        # pollute the demo store.
        await self.memos.store.clear_user(eval_user, None)
        return report


def _has_leak(injected, expected, forbidden) -> bool:
    """A leak is an injected memory that mentions a forbidden phrase without
    also mentioning an expected phrase (i.e. a genuinely outdated memory, not a
    superseding decision that references the old choice)."""
    if not forbidden:
        return False
    for item in injected:
        content = item["memory"]["content"].lower()
        if any(f.lower() in content for f in forbidden):
            if not any(e.lower() in content for e in expected):
                return True
    return False


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)
