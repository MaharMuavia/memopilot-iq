"""Unit tests for Qwen provider response handling."""
from __future__ import annotations

import os
import sys

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
