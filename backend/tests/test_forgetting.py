"""Tests for the forgetting engine and supersession."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import MemoryRecord, MemoryStatus, MemoryType


@pytest.mark.asyncio
async def test_expired_deadline_is_expired(memos):
    mem = MemoryRecord(
        user_id="u", session_id="s", project_id="p",
        type=MemoryType.deadline, content="ship by yesterday",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    await memos.store.add(mem)
    changes = await memos.forgetting.sweep("u", "p")
    refreshed = await memos.store.get(mem.memory_id)
    assert refreshed.status == MemoryStatus.expired
    assert any(c["memory_id"] == mem.memory_id for c in changes)


@pytest.mark.asyncio
async def test_critical_memory_not_archived(memos):
    mem = MemoryRecord(
        user_id="u", session_id="s", project_id="p",
        type=MemoryType.critical, content="never commit api keys",
        is_critical=True, importance=0.1, usage_count=0,
        updated_at=datetime.now(timezone.utc) - timedelta(days=90),
    )
    await memos.store.add(mem)
    await memos.forgetting.sweep("u", "p")
    refreshed = await memos.store.get(mem.memory_id)
    assert refreshed.status == MemoryStatus.active


@pytest.mark.asyncio
async def test_supersession_on_contradiction(memos):
    # Establish React + Vite, then contradict with Next.js.
    await memos.remember(user_id="u", project_id="p", session_id="s1",
                         message="Use React + Vite for the frontend.")
    actions = await memos.remember(user_id="u", project_id="p", session_id="s2",
                                   message="I changed my mind. Use Next.js instead of React + Vite.")
    assert actions.superseded, "old framework memory should be superseded"

    active = await memos.store.list(
        "u", "p", statuses=[MemoryStatus.active.value, MemoryStatus.pinned.value]
    )
    contents = " ".join(m.content.lower() for m in active)
    assert "next.js" in contents
    # The superseded react memory must not be in the ACTIVE set (it is retained
    # with status=superseded for the timeline, but never retrieved).
    assert not any(m.status == MemoryStatus.superseded for m in active)
    # It is still retained (non-destructive forgetting).
    all_mems = await memos.store.list("u", "p", include_all=True)
    assert any(m.status == MemoryStatus.superseded for m in all_mems)
