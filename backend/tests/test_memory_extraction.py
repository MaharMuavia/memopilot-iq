"""Tests for the memory extraction pipeline (offline deterministic mode)."""
from __future__ import annotations

import pytest

from app.models import MemoryRecord, MemoryStatus, MemoryType


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


@pytest.mark.asyncio
async def test_provider_updates_cannot_mutate_another_tenant(memos):
    victim = MemoryRecord(
        memory_id="mem_victim",
        user_id="victim",
        project_id="p",
        session_id="s1",
        type=MemoryType.preference,
        content="Victim prefers FastAPI.",
    )
    await memos.store.add(victim)

    async def malicious_update(*_args, **_kwargs):
        return {
            "new_memories": [],
            "updates": [{
                "old_memory_id": victim.memory_id,
                "action": "supersede",
                "reason": "cross-tenant provider output",
            }],
            "forget": [{"memory_id": victim.memory_id, "action": "archive"}],
        }

    memos.qwen.extract_json = malicious_update
    await memos.remember(
        user_id="attacker",
        project_id="p",
        session_id="s2",
        message="I now prefer Django for this project.",
    )

    unchanged = await memos.store.get(victim.memory_id)
    assert unchanged is not None
    assert unchanged.status == MemoryStatus.active
    assert unchanged.user_id == "victim"


@pytest.mark.asyncio
async def test_qwen_update_handles_general_contradiction_outside_fixed_taxonomy(memos):
    old = MemoryRecord(
        memory_id="mem_old_audience",
        user_id="u",
        project_id="p",
        session_id="s1",
        type=MemoryType.decision,
        content="The target audience is universities.",
    )
    await memos.store.add(old)

    async def audience_update(*_args, **_kwargs):
        return {
            "new_memories": [{
                "type": "decision",
                "content": "The target audience is now hospitals.",
                "summary": "Target audience: hospitals",
                "importance": 0.9,
                "confidence": 0.95,
            }],
            "updates": [{
                "old_memory_id": old.memory_id,
                "action": "supersede",
                "reason": "The new statement changes the target audience.",
            }],
            "forget": [],
        }

    memos.qwen.extract_json = audience_update
    actions = await memos.remember(
        user_id="u",
        project_id="p",
        session_id="s2",
        message="Our target audience is now hospitals instead of universities.",
    )

    assert any(item.get("via") == "llm_update" for item in actions.superseded)
    refreshed = await memos.store.get(old.memory_id)
    assert refreshed is not None
    assert refreshed.status == MemoryStatus.superseded
    active = await memos.store.list("u", "p")
    assert any("hospitals" in memory.content.lower() for memory in active)
