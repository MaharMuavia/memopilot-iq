"""Trace helpers shared by the context builder.

A trace makes MemoryOS transparent: for every answer the UI can show which
memories were injected, which were skipped, the score breakdown, the reason,
and how the token budget was spent.
"""
from __future__ import annotations

from ..models import MemoryRecord, ScoredMemory


def approx_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token), good enough for budgeting."""
    return max(1, len(text) // 4)


def memory_context_text(memory: MemoryRecord) -> str:
    """Use the canonical compact proposition while retaining full audit content."""
    return memory.summary.strip() or memory.content


def to_scored_memory(
    memory: MemoryRecord,
    components: dict,
    included: bool,
    reason: str,
) -> ScoredMemory:
    return ScoredMemory(
        memory=memory.public_view(),
        score=components.get("final_score", 0.0),
        components={
            k: round(v, 4)
            for k, v in components.items()
            if not k.startswith("_") and k != "final_score"
        },
        included=included,
        reason=reason,
        approx_tokens=approx_tokens(memory_context_text(memory)),
    )
