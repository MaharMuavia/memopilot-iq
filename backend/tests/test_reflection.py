"""Tests for the Memory Reflection / consolidation engine."""
from __future__ import annotations

import pytest

from app.models import MemoryRecord, MemoryStatus, MemoryType


def _mem(content, *, importance=0.5, usage=0, mtype=MemoryType.preference):
    return MemoryRecord(
        user_id="u", session_id="s", project_id="p", content=content,
        summary=content[:40], importance=importance, usage_count=usage, type=mtype,
    )


@pytest.mark.asyncio
async def test_reflection_merges_near_duplicates(memos):
    await memos.store.add(_mem("I prefer the FastAPI backend framework", importance=0.7))
    await memos.store.add(_mem("I prefer the FastAPI backend framework!", importance=0.5))
    report = await memos.reflection.reflect("u", "p")
    assert len(report["merged"]) == 1
    active = await memos.store.list(
        "u", "p", statuses=[MemoryStatus.active.value, MemoryStatus.pinned.value]
    )
    fastapi = [m for m in active if "fastapi" in m.content.lower()]
    assert len(fastapi) == 1  # the duplicate was archived


@pytest.mark.asyncio
async def test_reflection_promotes_frequently_used(memos):
    await memos.store.add(_mem("Use Alibaba Cloud", importance=0.5, usage=3))
    report = await memos.reflection.reflect("u", "p")
    assert report["promoted"]
    assert report["promoted"][0]["to"] > report["promoted"][0]["from"]


@pytest.mark.asyncio
async def test_reflection_derives_insight_from_cluster(memos):
    await memos.store.add(_mem("I prefer the FastAPI backend"))
    await memos.store.add(_mem("Use Alibaba Cloud for deployment"))
    await memos.store.add(_mem("Keep all answers short and practical"))
    report = await memos.reflection.reflect("u", "p")
    assert report["insights"]
    mems = await memos.store.list("u", "p")
    assert any("insight" in m.tags for m in mems)


@pytest.mark.asyncio
async def test_reflection_is_idempotent_for_insights(memos):
    await memos.store.add(_mem("I prefer the FastAPI backend"))
    await memos.store.add(_mem("Use Alibaba Cloud for deployment"))
    await memos.store.add(_mem("Keep all answers short and practical"))
    first = await memos.reflection.reflect("u", "p")
    second = await memos.reflection.reflect("u", "p")
    assert first["insights"]
    assert second["insights"] == []  # no duplicate insight created
