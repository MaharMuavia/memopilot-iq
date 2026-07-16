"""Evaluation benchmark runner.

Runs the scenarios in ``scenarios.json`` twice:
  * memory-agent: seeds memories, builds context with MemoryOS, then answers.
  * baseline: answers with NO long-term memory (current message only).

It measures preference adherence, cross-session recall, supersession success,
expired-memory avoidance, critical recall, recall in the assembled context,
token savings and latency,
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


_BASE_SYSTEM = "You are a helpful assistant."


def _keywords_present(text: str, keywords: List[str]) -> bool:
    low = text.lower()
    return all(k.lower() in low for k in keywords) if keywords else True


def answer_correct(answer: str, expected: List[str], forbidden: List[str]) -> bool:
    """Strict lexical grader used only for the diagnostic suite.

    An answer that contains both expected and forbidden terms is ambiguous and
    is not counted as correct. This deliberately underestimates performance,
    but prevents an answer that recommends an outdated option from receiving a
    false pass merely because it also mentions the preferred option.
    """
    low = (answer or "").lower()
    has_expected = all(e.lower() in low for e in expected) if expected else True
    has_forbidden = any(f.lower() in low for f in forbidden)
    return has_expected and not has_forbidden


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

        latencies: List[float] = []
        recall_hits = 0
        recall_total = 0
        outdated_errors = 0
        memory_tokens_total = 0
        contexts: List[Dict[str, Any]] = []

        # ---- Pass 1: memory-layer diagnostics (no LLM calls) ----
        for sc in scenarios:
            eval_project = f"eval-{sc['id']}"  # isolate each scenario
            for msg in sc["setup_messages"]:
                await self.memos.remember(
                    user_id=eval_user, project_id=eval_project,
                    session_id="eval", message=msg,
                )
            # Simulate time passing so temporary memories expire.
            await self._age_temporary(eval_user, eval_project)

            start = time.perf_counter()
            system_prompt, trace, used = await self.memos.build_context(
                eval_user, eval_project, sc["test_question"]
            )
            latency = (time.perf_counter() - start) * 1000.0
            latencies.append(trace.retrieval_latency_ms or latency)

            injected = [i.model_dump() for i in trace.included]
            expected = sc["expected_answer_keywords"]
            forbidden = sc["must_not_use_keywords"]
            leaked = _has_leak(injected, expected, forbidden)

            if expected:
                recall_total += 1
                injected_text = " ".join(m["memory"]["content"] for m in injected)
                if _keywords_present(injected_text, expected):
                    recall_hits += 1
            if leaked:
                outdated_errors += 1
            memory_tokens_total += trace.tokens_used

            contexts.append({
                "id": sc["id"], "title": sc["title"],
                "system_prompt": system_prompt, "question": sc["test_question"],
                "expected": expected, "forbidden": forbidden,
                "tokens_used": trace.tokens_used, "leaked": leaked,
            })

        n = len(scenarios)
        # Compare only the variable historical context. The system prompt and
        # current question are shared by both approaches and must not be
        # inflated with an arbitrary constant.
        full_history_tokens = sum(
            _approx_tokens(" ".join(sc["setup_messages"]))
            for sc in scenarios
        )
        token_savings_percent = (
            round(100 * (1 - memory_tokens_total / full_history_tokens))
            if full_history_tokens else 0
        )

        # ---- Pass 2: cross-backbone answer accuracy (LLM calls) ----
        backbones = await self._run_backbones(contexts)
        primary = backbones[0] if backbones else None
        primary_per = {p["id"]: p for p in (primary["per_scenario"] if primary else [])}

        scenarios_out = [
            {
                "id": c["id"], "title": c["title"],
                "memory_agent_correct": primary_per.get(c["id"], {}).get("agent_correct", False),
                "baseline_correct": primary_per.get(c["id"], {}).get("baseline_correct", False),
                "tokens_used": c["tokens_used"],
                "forbidden_leaked": c["leaked"],
            }
            for c in contexts
        ]

        report = {
            "memory_agent_accuracy": primary["agent_accuracy"] if primary else 0.0,
            "baseline_no_memory_accuracy": primary["baseline_accuracy"] if primary else 0.0,
            "memory_recall_at_context": round(recall_hits / recall_total, 2) if recall_total else 1.0,
            "outdated_memory_errors": outdated_errors,
            "outdated_memory_avoidance": round(1 - outdated_errors / n, 2),
            "preference_adherence": primary["agent_accuracy"] if primary else 0.0,
            "token_savings_percent": max(0, token_savings_percent),
            "response_accuracy_delta": primary["delta"] if primary else 0.0,
            "avg_retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "num_scenarios": n,
            "retrieval_top_k": self.memos.settings.retrieval_top_k,
            "evaluator": "strict-keyword-v1",
            "backbones": backbones,
            "scenarios": scenarios_out,
        }

        await self.memos.store.clear_user(eval_user, None)
        return report

    async def _run_backbones(
        self, contexts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """For each available answer-generating backbone, grade the agent (with
        MemoryOS context) vs a no-memory baseline on the actual answers. The
        MemoryOS layer is identical across backbones; only the LLM varies."""
        from .providers import backbone_chat, configured_backbones

        settings = self.memos.settings

        async def primary_chat(messages):
            return await self.memos.qwen.chat(messages)

        runners: List[Dict[str, Any]] = [{
            "name": "qwen" if settings.qwen_configured else "offline",
            "label": (f"Qwen ({settings.qwen_chat_model})"
                      if settings.qwen_configured else "Offline fallback"),
            "chat": primary_chat,
        }]
        for p in configured_backbones(settings):
            if p["name"] == "qwen":
                continue  # already the primary runner
            runners.append({
                "name": p["name"], "label": p["label"],
                "chat": (lambda prov: (lambda m: backbone_chat(prov, m)))(p),
            })

        results: List[Dict[str, Any]] = []
        for b in runners:
            agent_c = base_c = ok = skipped = 0
            per: List[Dict[str, Any]] = []
            for c in contexts:
                agent = await b["chat"]([
                    {"role": "system", "content": c["system_prompt"]},
                    {"role": "user", "content": c["question"]},
                ])
                base = await b["chat"]([
                    {"role": "system", "content": _BASE_SYSTEM},
                    {"role": "user", "content": c["question"]},
                ])
                if agent is None or base is None:
                    skipped += 1  # provider hiccup on this item; skip, keep going
                    continue
                a_ok = answer_correct(agent, c["expected"], c["forbidden"])
                b_ok = answer_correct(base, c["expected"], c["forbidden"])
                agent_c += int(a_ok)
                base_c += int(b_ok)
                ok += 1
                per.append({"id": c["id"], "agent_correct": a_ok, "baseline_correct": b_ok})
            if ok == 0:
                results.append({"name": b["name"], "label": b["label"], "error": True})
                continue
            results.append({
                "skipped": skipped,
                "name": b["name"], "label": b["label"], "n": ok,
                "agent_accuracy": round(agent_c / ok, 2),
                "baseline_accuracy": round(base_c / ok, 2),
                "delta": round((agent_c - base_c) / ok, 2),
                "per_scenario": per,
            })
        return results


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
