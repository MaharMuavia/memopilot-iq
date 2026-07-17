"""Regression tests for the local SQLite memory store."""
from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_event_writes_are_concurrency_safe_and_untruncated(memos):
    event_count = 240

    await asyncio.gather(
        *(
            memos.store.add_event(
                {
                    "kind": "test_event",
                    "user_id": "audit-user",
                    "project_id": "audit-project",
                    "sequence": sequence,
                }
            )
            for sequence in range(event_count)
        )
    )

    events = await memos.store.list_events("audit-user", "audit-project")

    assert len(events) == event_count
    assert {event["sequence"] for event in events} == set(range(event_count))


@pytest.mark.asyncio
async def test_event_queries_are_project_scoped(memos):
    for project_id in ("project-a", "project-b", None):
        await memos.store.add_event(
            {
                "kind": "test_event",
                "user_id": "scoped-user",
                "project_id": project_id,
            }
        )

    scoped = await memos.store.list_events("scoped-user", "project-a")

    assert {event["project_id"] for event in scoped} == {"project-a", None}
