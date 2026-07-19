"""Evaluation benchmark runner.

Runs each scenario against four answer strategies:
  * memory-agent: governed MemoryOS context.
  * no-memory baseline: current question only.
  * full-history baseline: all raw setup turns.
  * history-summary baseline: an LLM-generated summary of the setup turns.

It measures preference adherence, cross-session recall, supersession success,
expired-memory avoidance, critical recall, recall in the assembled context,
token savings and latency,
then aggregates into the report consumed by the Evaluation Dashboard.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..memory import MemoryOS

_SCENARIOS_PATH = os.path.join(os.path.dirname(__file__), "scenarios.json")


def load_scenarios() -> Dict[str, Any]:
    with open(_SCENARIOS_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


_BASE_SYSTEM = "You are a helpful assistant."


def _term_matches(text: str, term: str) -> list[re.Match[str]]:
    """Match a phrase on alphanumeric boundaries.

    Plain substring checks make ``npm`` match ``pnpm`` and therefore report a
    false stale-memory error. Punctuation inside a phrase remains significant,
    while surrounding letters and digits are excluded.
    """
    normalized = term.strip()
    if not normalized:
        return []
    pattern = re.escape(normalized).replace(r"\ ", r"\s+")
    if normalized[0].isalnum():
        pattern = rf"(?<![a-z0-9]){pattern}"
    if normalized[-1].isalnum():
        # Treat a simple plural as the same lexical concept (key/keys,
        # token/tokens) while retaining the boundary that keeps npm != pnpm.
        pattern = rf"{pattern}s?(?![a-z0-9])"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE))


def _keywords_present(
    text: str,
    keywords: List[str],
    alternatives: Dict[str, List[str]] | None = None,
) -> bool:
    aliases = alternatives or {}
    return all(
        any(_term_matches(text, candidate) for candidate in [keyword, *aliases.get(keyword, [])])
        for keyword in keywords
    ) if keywords else True


def _forbidden_is_asserted(text: str, forbidden: str) -> bool:
    """Return whether a forbidden alternative is presented as current advice.

    Merely saying "avoid dark" or "npm was replaced" is evidence of correct
    contradiction handling, not a stale recommendation. The deterministic
    grader recognizes common rejection language while remaining conservative.
    """
    for match in _term_matches(text, forbidden):
        before = text[max(0, match.start() - 48):match.start()].lower()
        after = text[match.end():match.end() + 48].lower()
        rejected_before = re.search(
            r"(?:avoid|without|not|never|no longer|instead of|rather than|"
            r"do not|don't|replaced|superseded|deprecated)\s+(?:\w+\s+){0,3}$",
            before,
        )
        rejected_after = re.match(
            r"\s+(?:is|was|has been|should be)?\s*"
            r"(?:outdated|replaced|superseded|deprecated|incorrect|not recommended)",
            after,
        )
        if not rejected_before and not rejected_after:
            return True
    return False


def answer_correct(
    answer: str,
    expected: List[str],
    forbidden: List[str],
    expected_alternatives: Dict[str, List[str]] | None = None,
) -> bool:
    """Deterministic phrase-and-negation grader for the diagnostic suite."""
    text = answer or ""
    has_expected = _keywords_present(text, expected, expected_alternatives)
    has_forbidden = any(_forbidden_is_asserted(text, term) for term in forbidden)
    return has_expected and not has_forbidden


def _answer_failure_reason(
    answer: str,
    expected: List[str],
    forbidden: List[str],
    expected_alternatives: Dict[str, List[str]] | None = None,
) -> str | None:
    aliases = expected_alternatives or {}
    missing = [
        term
        for term in expected
        if not any(
            _term_matches(answer or "", candidate)
            for candidate in [term, *aliases.get(term, [])]
        )
    ]
    asserted = [term for term in forbidden if _forbidden_is_asserted(answer or "", term)]
    if not missing and not asserted:
        return None
    parts = []
    if missing:
        parts.append(f"missing expected phrase(s): {', '.join(missing)}")
    if asserted:
        parts.append(f"asserted outdated phrase(s): {', '.join(asserted)}")
    return "; ".join(parts)


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
        run_started = time.perf_counter()
        fallbacks_before = self.memos.qwen.fallback_count
        usage_before = self.memos.qwen.usage
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
            # Only explicit lifecycle scenarios simulate time passing. Aging
            # every scenario invalidates legitimate temporary/deadline recall.
            if sc.get("expire_temporary_before_test", False):
                await self._age_temporary(eval_user, eval_project)

            start = time.perf_counter()
            system_prompt, trace, used = await self.memos.build_context(
                eval_user, eval_project, sc["test_question"]
            )
            latency = (time.perf_counter() - start) * 1000.0
            latencies.append(trace.retrieval_latency_ms or latency)

            injected = [i.model_dump() for i in trace.included]
            expected = sc["expected_answer_keywords"]
            expected_alternatives = sc.get("expected_answer_alternatives", {})
            forbidden = sc["must_not_use_keywords"]
            leaked = _has_leak(injected, expected, forbidden)

            if expected:
                recall_total += 1
                injected_text = " ".join(m["memory"]["content"] for m in injected)
                if _keywords_present(injected_text, expected, expected_alternatives):
                    recall_hits += 1
            if leaked:
                outdated_errors += 1
            memory_tokens_total += trace.tokens_used

            contexts.append({
                "id": sc["id"], "title": sc["title"],
                "system_prompt": system_prompt, "question": sc["test_question"],
                "setup_messages": sc["setup_messages"],
                "expected": expected, "forbidden": forbidden,
                "expected_alternatives": expected_alternatives,
                "tokens_used": trace.tokens_used, "leaked": leaked,
                "context_recall": _keywords_present(
                    " ".join(
                        item["memory"].get("summary") or item["memory"]["content"]
                        for item in injected
                    ),
                    expected,
                    expected_alternatives,
                ) if expected else True,
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
                "full_history_correct": primary_per.get(c["id"], {}).get("full_history_correct", False),
                "history_summary_correct": primary_per.get(c["id"], {}).get("history_summary_correct", False),
                "agent_answer": primary_per.get(c["id"], {}).get("agent_answer", ""),
                "answer_failure_reason": primary_per.get(c["id"], {}).get("answer_failure_reason"),
                "context_recall": c["context_recall"],
                "tokens_used": c["tokens_used"],
                "forbidden_leaked": c["leaked"],
            }
            for c in contexts
        ]

        provider_fallbacks = self.memos.qwen.fallback_count - fallbacks_before
        provider_status = (
            "degraded_offline_fallback"
            if provider_fallbacks
            else self.memos.qwen.provider_status
        )
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "build_sha": os.getenv("APP_BUILD_SHA", "development"),
            "duration_seconds": round(time.perf_counter() - run_started, 2),
            "primary_backbone": primary["label"] if primary else "unavailable",
            "provider_status": provider_status,
            "provider_fallbacks": provider_fallbacks,
            "memory_agent_accuracy": primary["agent_accuracy"] if primary else 0.0,
            "baseline_no_memory_accuracy": primary["baseline_accuracy"] if primary else 0.0,
            "baseline_full_history_accuracy": primary["full_history_accuracy"] if primary else 0.0,
            "baseline_history_summary_accuracy": primary["history_summary_accuracy"] if primary else 0.0,
            "memory_recall_at_context": round(recall_hits / recall_total, 2) if recall_total else 1.0,
            "memory_recall_hits": recall_hits,
            "memory_recall_total": recall_total,
            "outdated_memory_errors": outdated_errors,
            "outdated_memory_avoidance": round(1 - outdated_errors / n, 2),
            "preference_adherence": primary["agent_accuracy"] if primary else 0.0,
            "token_savings_percent": max(0, token_savings_percent),
            "memory_context_tokens": memory_tokens_total,
            "full_history_tokens": full_history_tokens,
            "response_accuracy_delta": primary["delta"] if primary else 0.0,
            "provider_token_usage": _usage_delta(usage_before, self.memos.qwen.usage),
            "model_calls_per_scenario_per_backbone": 5,
            "avg_retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "retrieval_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "num_scenarios": n,
            "retrieval_top_k": self.memos.settings.retrieval_top_k,
            "memory_token_budget": self.memos.settings.memory_token_budget,
            "chat_model": self.memos.settings.qwen_chat_model,
            "embedding_model": self.memos.settings.qwen_embedding_model,
            "evaluator": "deterministic-phrase-negation-v2",
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

        # Model calls dominate benchmark time. Run a small bounded batch so the
        # 24-scenario judge flow completes within normal proxy timeouts without
        # flooding provider rate limits.
        try:
            configured_concurrency = int(os.getenv("EVAL_MAX_CONCURRENCY", "4"))
        except ValueError:
            configured_concurrency = 4
        max_concurrency = max(1, min(configured_concurrency, 8))
        semaphore = asyncio.Semaphore(max_concurrency)

        async def limited_chat(chat, messages):
            async with semaphore:
                return await chat(messages)

        results: List[Dict[str, Any]] = []
        for b in runners:
            agent_c = base_c = history_c = summary_c = ok = skipped = 0
            per: List[Dict[str, Any]] = []

            async def evaluate(c):
                history = "\n".join(f"- {message}" for message in c["setup_messages"])
                agent_messages = [
                    {"role": "system", "content": c["system_prompt"]},
                    {"role": "user", "content": c["question"]},
                ]
                baseline_messages = [
                    {"role": "system", "content": _BASE_SYSTEM},
                    {"role": "user", "content": c["question"]},
                ]
                full_history_messages = [
                    {
                        "role": "system",
                        "content": (
                            f"{_BASE_SYSTEM}\nUse this raw prior conversation history when relevant. "
                            f"Later statements override earlier ones.\n{history}"
                        ),
                    },
                    {"role": "user", "content": c["question"]},
                ]
                summary_messages = [
                    {
                        "role": "system",
                        "content": (
                            "Summarize the durable current user facts and decisions in the "
                            "provided history. Resolve contradictions in favor of the latest "
                            "statement. Do not answer any question or invent information."
                        ),
                    },
                    {"role": "user", "content": history},
                ]
                agent, base, full_history, history_summary = await asyncio.gather(
                    limited_chat(b["chat"], agent_messages),
                    limited_chat(b["chat"], baseline_messages),
                    limited_chat(b["chat"], full_history_messages),
                    limited_chat(b["chat"], summary_messages),
                )
                summary_answer = await limited_chat(
                    b["chat"],
                    [
                        {
                            "role": "system",
                            "content": f"{_BASE_SYSTEM}\nPrior-user summary:\n{history_summary}",
                        },
                        {"role": "user", "content": c["question"]},
                    ],
                )
                return c, agent, base, full_history, summary_answer

            evaluated = await asyncio.gather(*(evaluate(c) for c in contexts))
            for c, agent, base, full_history, summary_answer in evaluated:
                if any(
                    answer is None
                    for answer in (agent, base, full_history, summary_answer)
                ):
                    skipped += 1  # provider hiccup on this item; skip, keep going
                    continue
                a_ok = answer_correct(
                    agent, c["expected"], c["forbidden"], c["expected_alternatives"]
                )
                b_ok = answer_correct(
                    base, c["expected"], c["forbidden"], c["expected_alternatives"]
                )
                h_ok = answer_correct(
                    full_history, c["expected"], c["forbidden"], c["expected_alternatives"]
                )
                s_ok = answer_correct(
                    summary_answer, c["expected"], c["forbidden"], c["expected_alternatives"]
                )
                agent_c += int(a_ok)
                base_c += int(b_ok)
                history_c += int(h_ok)
                summary_c += int(s_ok)
                ok += 1
                per.append({
                    "id": c["id"],
                    "agent_correct": a_ok,
                    "baseline_correct": b_ok,
                    "full_history_correct": h_ok,
                    "history_summary_correct": s_ok,
                    "agent_answer": agent,
                    "answer_failure_reason": _answer_failure_reason(
                        agent,
                        c["expected"],
                        c["forbidden"],
                        c["expected_alternatives"],
                    ),
                })
            if ok == 0:
                results.append({"name": b["name"], "label": b["label"], "error": True})
                continue
            results.append({
                "skipped": skipped,
                "name": b["name"], "label": b["label"], "n": ok,
                "agent_accuracy": round(agent_c / ok, 2),
                "baseline_accuracy": round(base_c / ok, 2),
                "full_history_accuracy": round(history_c / ok, 2),
                "history_summary_accuracy": round(summary_c / ok, 2),
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
        content = item["memory"]["content"]
        if any(_forbidden_is_asserted(content, term) for term in forbidden):
            if not any(_term_matches(content, term) for term in expected):
                return True
    return False


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _usage_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Subtract cumulative provider counters for one reproducible benchmark run."""
    output: Dict[str, Any] = {"operations": {}, "totals": {}}
    for operation, values in after.get("operations", {}).items():
        previous = before.get("operations", {}).get(operation, {})
        delta = {
            key: value - previous.get(key, 0)
            for key, value in values.items()
            if value - previous.get(key, 0) > 0
        }
        if delta:
            output["operations"][operation] = delta
    for key, value in after.get("totals", {}).items():
        delta = value - before.get("totals", {}).get(key, 0)
        if delta > 0:
            output["totals"][key] = delta
    return output
