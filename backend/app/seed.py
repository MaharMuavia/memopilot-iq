"""Scripted demo seeder.

Replays the 5-session demo scenario from the spec so a fresh database is
immediately demo-ready (and the demo video can be shot in under 3 minutes).
"""
from __future__ import annotations

from .memory import MemoryOS

USER = "demo-user"
PROJECT = "qwen-memoryagent"

DEMO_SESSIONS = [
    (
        "session-001",
        "I am building a Qwen Hackathon Track 1 MemoryAgent project. I prefer "
        "FastAPI backend, React + Vite frontend, Alibaba Cloud deployment, clean "
        "light UI, and short practical answers. Never commit API keys.",
    ),
    (
        "session-003",
        "Actually for this project, add an evaluation dashboard and make memory "
        "forgetting the strongest feature.",
    ),
    (
        "session-004",
        "I changed my mind. Use Next.js instead of React + Vite.",
    ),
]


async def seed_demo(memos: MemoryOS) -> None:
    # Clear any prior demo data so seeding is idempotent.
    await memos.store.clear_user(USER, PROJECT)
    for session_id, message in DEMO_SESSIONS:
        await memos.remember(
            user_id=USER,
            project_id=PROJECT,
            session_id=session_id,
            message=message,
        )
