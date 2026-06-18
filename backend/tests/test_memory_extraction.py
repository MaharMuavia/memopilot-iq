"""Tests for the memory extraction pipeline (offline deterministic mode)."""
from __future__ import annotations

import pytest

from app.models import MemoryStatus, MemoryType


@pytest.mark.asyncio
async def test_extracts_multiple_typed_memories(memos):
    actions = await memos.remember(
        user_id="u", project_id="p", session_id="s1",
        message=(
            "I prefer FastAPI backend, React + Vite frontend, Alibaba Cloud "
            "deployment, light UI, short answers. Never commit API keys."
        ),
    )
    assert len(actions.created) >= 4
    mems = await memos.store.list("u", "p")
    # The critical safety rule must be captured as critical.
    assert any(m.is_critical and "api key" in m.content.lower() for m in mems)


@pytest.mark.asyncio
async def test_questions_are_not_stored(memos):
    actions = await memos.remember(
        user_id="u", project_id="p", session_id="s1",
        message="What backend should I use and how do I deploy it?",
    )
    # Pure questions carry no durable facts.
    assert actions.created == []


@pytest.mark.asyncio
async def test_temporary_memory_gets_expiry(memos):
    await memos.remember(
        user_id="u", project_id="p", session_id="s1",
        message="Temporary note: the staging server is down today only.",
    )
    mems = await memos.store.list("u", "p", include_all=True)
    temp = [m for m in mems if m.type == MemoryType.temporary]
    assert temp, "expected a temporary memory"
    assert temp[0].expires_at is not None


@pytest.mark.asyncio
async def test_duplicate_is_merged_not_duplicated(memos):
    await memos.remember(user_id="u", project_id="p", session_id="s1",
                         message="I prefer FastAPI backend.")
    actions = await memos.remember(user_id="u", project_id="p", session_id="s2",
                                   message="I prefer FastAPI backend.")
    # Second time should merge (update) rather than create a duplicate.
    assert actions.updated
    fastapi_mems = [
        m for m in await memos.store.list("u", "p")
        if "fastapi" in m.content.lower() and m.status == MemoryStatus.active
    ]
    assert len(fastapi_mems) == 1
