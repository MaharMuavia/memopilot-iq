"""Tests for the secret safety / privacy engine."""
from __future__ import annotations

import pytest

from app.memory.safety import safety_engine


@pytest.mark.parametrize(
    "text",
    [
        "my key is sk-abcdef0123456789abcdef0123456789",
        "AWS key AKIAIOSFODNN7EXAMPLE here",
        "alibaba LTAI5tAbc123Def456Ghi here",
        "token: ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "password = supersecretvalue123",
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",
    ],
)
def test_detects_secrets(text):
    assert safety_engine.has_secret(text)
    assert safety_engine.detect(text)


def test_redacts_secret_keeps_other_text():
    text = "I prefer FastAPI and my key is sk-abcdef0123456789abcdef0123456789"
    redacted = safety_engine.redact(text)
    assert "sk-abcdef0123456789" not in redacted
    assert "FastAPI" in redacted
    assert "REDACTED" in redacted


def test_clean_text_is_untouched():
    text = "I prefer FastAPI and React + Vite."
    assert not safety_engine.has_secret(text)
    assert safety_engine.redact(text) == text


@pytest.mark.asyncio
async def test_extractor_never_stores_secret(memos):
    actions = await memos.remember(
        user_id="u",
        project_id="p",
        session_id="s",
        message="My API key is sk-abcdef0123456789abcdef0123456789 and I prefer FastAPI.",
    )
    for created in actions.created:
        assert "sk-abcdef0123456789" not in created["content"]
    mems = await memos.store.list("u", "p", include_all=True)
    assert all("sk-abcdef0123456789" not in m.content for m in mems)
