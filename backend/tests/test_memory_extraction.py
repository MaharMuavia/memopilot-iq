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
async def test_provider_cannot_promote_preference_to_critical(memos):
    async def extracted_memories(*_args, **_kwargs):
        return {
            "new_memories": [
                {
                    "type": "preference",
                    "content": "User prefers short, concise answers.",
                    "summary": "Communication style: Short answers",
                    "importance": 1.0,
                    "confidence": 1.0,
                    "is_critical": True,
                },
                {
                    "type": "critical",
                    "content": "Never commit API keys.",
                    "summary": "Security constraint: Never commit API keys",
                    "importance": 1.0,
                    "confidence": 1.0,
                    "is_critical": False,
                },
            ]
        }

    memos.qwen.extract_json = extracted_memories
    await memos.remember(
        user_id="u",
        project_id="p",
        session_id="s1",
        message="I prefer short answers. Never commit API keys.",
    )

    memories = await memos.store.list("u", "p")
    preference = next(m for m in memories if m.type == MemoryType.preference)
    critical = next(m for m in memories if m.type == MemoryType.critical)

    assert preference.is_critical is False
    assert critical.is_critical is True


@pytest.mark.asyncio
async def test_questions_are_not_stored(memos):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Pure questions must not call the Memory Editor.")

    memos.qwen.extract_json = fail_if_called
    actions = await memos.remember(
        user_id="u", project_id="p", session_id="s1",
        message="What backend should I use and how do I deploy it?",
    )
    # Pure questions carry no durable facts.
    assert actions.created == []


@pytest.mark.asyncio
async def test_assistant_commands_do_not_call_memory_editor(memos):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Assistant commands must not call the Memory Editor.")

    memos.qwen.extract_json = fail_if_called
    actions = await memos.remember(
        user_id="u",
        project_id="p",
        session_id="s1",
        message="Design the backend architecture.",
    )

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
