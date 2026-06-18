"""Tests for the supersession engine."""
from __future__ import annotations

import pytest

from app.memory.supersession import find_contradictions
from app.memory.classifier import topic_of
from app.models import MemoryRecord, MemoryStatus, MemoryType


def _mem(content, status=MemoryStatus.active, critical=False):
    return MemoryRecord(
        user_id="u", session_id="s", project_id="p", content=content,
        status=status, is_critical=critical,
        type=MemoryType.critical if critical else MemoryType.preference,
    )


def test_topic_of_prefers_first_mention():
    assert topic_of("Use Next.js instead of React + Vite")[1] == "next.js"
    assert topic_of("Use React + Vite for the frontend")[1] == "react"


def test_contradiction_detected_same_topic():
    existing = [_mem("Use React + Vite for the frontend")]
    new = _mem("Use Next.js instead of React + Vite")
    hits = find_contradictions(existing, new)
    assert len(hits) == 1


def test_no_contradiction_different_topic():
    existing = [_mem("Use FastAPI for the backend")]
    new = _mem("Use Next.js for the frontend")
    assert find_contradictions(existing, new) == []


def test_critical_memory_never_superseded():
    existing = [_mem("Never use Azure", critical=True)]
    new = _mem("Actually use Azure now")
    assert find_contradictions(existing, new) == []


def test_superseded_memory_not_reconsidered():
    existing = [_mem("Use React + Vite", status=MemoryStatus.superseded)]
    new = _mem("Use Vue instead")
    assert find_contradictions(existing, new) == []


@pytest.mark.asyncio
async def test_end_to_end_supersession(memos):
    await memos.remember(user_id="u", project_id="p", session_id="s1",
                         message="Use React + Vite for the frontend.")
    actions = await memos.remember(user_id="u", project_id="p", session_id="s2",
                                   message="Actually, use Next.js instead of React + Vite.")
    assert actions.superseded
    active = await memos.store.list(
        "u", "p", statuses=[MemoryStatus.active.value, MemoryStatus.pinned.value]
    )
    joined = " ".join(m.content.lower() for m in active)
    assert "next.js" in joined
