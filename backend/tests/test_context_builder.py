"""Tests for the context budget manager."""
from __future__ import annotations

import pytest

from app.memory.context_builder import ContextBuilder
from app.memory.scorer import score_memory
from app.models import MemoryRecord, MemoryStatus, MemoryType


def _scored(content, project="p", critical=False, sim=0.5, importance=0.5):
    mem = MemoryRecord(
        user_id="u", session_id="s", project_id=project, content=content,
        is_critical=critical, importance=importance,
        type=MemoryType.critical if critical else MemoryType.preference,
        status=MemoryStatus.pinned if critical else MemoryStatus.active,
    )
    components = score_memory(mem, sim, "p")
    components["dense_similarity"] = sim
    components["keyword_overlap"] = 0.0
    return mem, components


def test_critical_memory_respects_strict_budget():
    builder = ContextBuilder(token_budget=1, top_k=3)  # tiny budget
    scored = [_scored("never commit api keys", critical=True, importance=0.95)]
    _, trace, used = builder.build("checklist", scored, "p", 1, 1.0)
    assert used == []
    assert trace.tokens_used <= builder.token_budget
    assert len(trace.skipped) == 1
    assert "critical/pinned" in trace.skipped[0].reason.lower()


def test_budget_skips_low_score_memories():
    builder = ContextBuilder(token_budget=20, top_k=10)
    big = "x" * 400  # ~100 tokens each
    scored = [_scored(big + str(i), sim=0.9 - i * 0.1) for i in range(5)]
    _, trace, used = builder.build("q", scored, "p", 5, 1.0)
    assert trace.tokens_used <= builder.token_budget
    assert len(trace.skipped) >= 1
    assert any("budget" in s.reason.lower() for s in trace.skipped)


def test_trace_records_included_and_skipped():
    builder = ContextBuilder(token_budget=2500, top_k=2)
    scored = [_scored(f"pref {i}", sim=0.9 - i * 0.05) for i in range(5)]
    _, trace, _ = builder.build("q", scored, "p", 5, 1.0)
    assert len(trace.included) == 2
    assert len(trace.skipped) == 3


def test_context_uses_canonical_summary_but_trace_retains_audit_content():
    builder = ContextBuilder(token_budget=2500, top_k=2)
    memory, components = _scored(
        "Use FastAPI for the backend instead of Flask.", sim=0.9
    )
    memory.summary = "Current backend framework: FastAPI"

    prompt, trace, used = builder.build(
        "Which backend framework is current?",
        [(memory, components)],
        "p",
        candidates_considered=1,
        retrieval_latency_ms=1.0,
    )

    assert used == [memory]
    assert "Current backend framework: FastAPI" in prompt
    assert "instead of Flask" not in prompt
    assert trace.included[0].memory["content"] == memory.content
    assert trace.included[0].approx_tokens == len(memory.summary) // 4


def test_unrelated_same_project_memories_are_not_injected():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    scored = [
        _scored("User's final demo label is CLOUD-PROOF-2026.", sim=0.57, importance=0.8),
        _scored("MemoPilot uses Alibaba Tablestore for persistent memory.", sim=0.42, importance=0.9),
    ]

    _, trace, used = builder.build(
        "Which frontend does this submitted build use?",
        scored,
        "p",
        candidates_considered=2,
        retrieval_latency_ms=1.0,
    )

    assert used == []
    assert len(trace.included) == 0
    assert len(trace.skipped) == 2
    assert all("below relevance threshold" in item.reason for item in trace.skipped)


def test_keyword_match_can_admit_memory_when_embedding_is_weak():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    memory, components = _scored(
        "The submitted frontend uses React 18 with Vite.", sim=0.40
    )
    components["keyword_overlap"] = 0.50

    _, trace, used = builder.build(
        "Which frontend does this submitted build use?",
        [(memory, components)],
        "p",
        candidates_considered=1,
        retrieval_latency_ms=1.0,
    )

    assert used == [memory]
    assert len(trace.included) == 1


def test_broad_architecture_request_admits_project_governance_preferences():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    memory, components = _scored(
        "Cloud provider preference: Alibaba Cloud", sim=0.40
    )

    _, trace, used = builder.build(
        "Design the backend architecture for my project.",
        [(memory, components)],
        "p",
        candidates_considered=1,
        retrieval_latency_ms=1.0,
    )

    assert used == [memory]
    assert "broad architecture/design request" in trace.included[0].reason


def test_scaffold_request_admits_project_framework_preference():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    memory, components = _scored("Frontend preference: React with Vite", sim=0.40)

    _, _, used = builder.build(
        "What should I scaffold the UI with?",
        [(memory, components)],
        "p",
        candidates_considered=1,
        retrieval_latency_ms=1.0,
    )

    assert used == [memory]


def test_broad_request_does_not_admit_other_project_memory():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    memory, components = _scored(
        "Cloud provider preference: Alibaba Cloud", project="other", sim=0.40
    )

    _, trace, used = builder.build(
        "Design the backend architecture for my project.",
        [(memory, components)],
        "p",
        candidates_considered=1,
        retrieval_latency_ms=1.0,
    )

    assert used == []
    assert len(trace.skipped) == 1


def test_system_prompt_contains_only_verified_current_implementation():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    prompt, _, _ = builder.build(
        "What stack is implemented?",
        [],
        "qwen-memoryagent",
        candidates_considered=0,
        retrieval_latency_ms=0.0,
    )

    assert "submitted public deployment runs on Alibaba Cloud ECS" in prompt
    assert "React 18 with Vite is served by Nginx" in prompt
    assert "FastAPI backend" in prompt
    assert "Next.js" not in prompt
    assert "SQLite" not in prompt
    assert "Alibaba Tablestore persists memory records" in prompt
    assert "calculates dense cosine similarity" in prompt
    assert "Alibaba OSS stores redacted turn snapshots" in prompt
    assert "Function Compute, ACK, PrivateLink, KMS" in prompt
    assert "not part of the submitted deployment" in prompt
    assert "MemoPilot memory layer" in prompt


def test_system_prompt_keeps_product_grounding_out_of_generic_projects():
    builder = ContextBuilder(token_budget=2500, top_k=8)
    prompt, _, _ = builder.build(
        "What frontend stack should I use?",
        [],
        "eval-supersede-frontend",
        candidates_considered=0,
        retrieval_latency_ms=0.0,
    )

    assert "VERIFIED MEMOPILOT IQ IMPLEMENTATION FACTS" not in prompt
