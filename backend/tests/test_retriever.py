"""Retrieval admission-signal regression tests."""
from __future__ import annotations

from app.memory.retriever import _keyword_overlap
from app.models import MemoryRecord


def _memory(content: str, tags: list[str] | None = None) -> MemoryRecord:
    return MemoryRecord(
        user_id="u",
        project_id="p",
        session_id="s",
        content=content,
        tags=tags or [],
    )


def test_meaningful_overlap_selects_frontend_plan_not_demo_label():
    query = (
        "What frontend does this submitted build use today, and what is "
        "planned after submission?"
    )
    plan = _memory("After this submission, migrate the frontend to Next.js.")
    unrelated = _memory("User's final demo label is CLOUD-PROOF-2026.")

    assert _keyword_overlap(query, plan) >= 0.20
    assert _keyword_overlap(query, unrelated) == 0.0


def test_architecture_tag_makes_deployment_preference_retrievable():
    memory = _memory(
        "I prefer Alibaba Cloud deployment.",
        tags=["alibaba", "deployment", "architecture"],
    )

    assert _keyword_overlap("Design the backend architecture.", memory) >= 0.20
