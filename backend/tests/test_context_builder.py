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
    return mem, score_memory(mem, sim, "p")


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
