"""Unit tests for Qwen provider response handling."""
from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.mark.asyncio
async def test_embed_many_sorts_provider_results_by_index(monkeypatch):
    from app.config import Settings
    from app.qwen_client import QwenClient

    settings = Settings(qwen_api_key="test-key")
    client = QwenClient(settings)

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "usage": {"prompt_tokens": 7, "total_tokens": 7},
                "data": [
                    {"index": 1, "embedding": [2.0]},
                    {"index": 0, "embedding": [1.0]},
                ]
            }

    class HttpClient:
        async def post(self, _path, json):
            assert json["input"] == ["first", "second"]
            return Response()

    async def fake_http():
        return HttpClient()

    monkeypatch.setattr(client, "_http", fake_http)
    assert await client.embed_many(["first", "second"]) == [[1.0], [2.0]]
    assert client.usage["operations"]["embedding"]["total_tokens"] == 7


@pytest.mark.asyncio
async def test_transient_timeout_is_retried_before_fallback(monkeypatch):
    from app.config import Settings
    from app.qwen_client import QwenClient

    client = QwenClient(Settings(qwen_api_key="test-key", qwen_max_retries=1))
    calls = 0

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 4,
                    "total_tokens": 14,
                },
                "choices": [{"message": {"content": "Live Qwen answer"}}],
            }

    class HttpClient:
        async def post(self, _path, json):
            assert json["enable_thinking"] is False
            assert json["max_tokens"] == 700
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ReadTimeout("temporary timeout")
            return Response()

    async def fake_http():
        return HttpClient()

    async def no_delay(_seconds):
        return None

    monkeypatch.setattr(client, "_http", fake_http)
    monkeypatch.setattr("app.qwen_client.asyncio.sleep", no_delay)

    answer = await client.chat([{"role": "user", "content": "Hello"}])

    assert answer == "Live Qwen answer"
    assert calls == 2
    assert client.provider_status == "online"
    assert client.fallback_count == 0
    assert client.usage["totals"] == {
        "prompt_tokens": 10,
        "completion_tokens": 4,
        "total_tokens": 14,
    }
