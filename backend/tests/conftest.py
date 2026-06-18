"""Pytest fixtures: an isolated MemoryOS using a temp SQLite DB, offline Qwen."""
from __future__ import annotations

import os
import sys

import pytest
import pytest_asyncio

# Make the `app` package importable when running `pytest` from backend/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import Settings  # noqa: E402
from app.memory import MemoryOS  # noqa: E402


@pytest_asyncio.fixture
async def memos(tmp_path):
    db = tmp_path / "test.db"
    settings = Settings(
        app_mode="local",
        qwen_api_key=None,  # forces deterministic offline mode
        memory_store="sqlite",
        database_url=f"sqlite:///{db}",
    )
    engine = MemoryOS(settings)
    await engine.init()
    yield engine
    await engine.qwen.aclose()
