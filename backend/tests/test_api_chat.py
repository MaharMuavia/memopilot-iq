"""End-to-end API tests using FastAPI's TestClient against offline Qwen."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "local")
    monkeypatch.setenv("MEMORY_STORE", "sqlite")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'api.db'}")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    # get_settings is cached; clear it so env overrides apply.
    from app.config import get_settings
    get_settings.cache_clear()

    from app.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] == "LOCAL_MODE"
    assert body["qwen_configured"] is False
    assert body["qwen_provider_status"] == "offline"


def test_chat_creates_and_uses_memory(client):
    # First turn: state preferences.
    r1 = client.post("/api/chat", json={
        "user_id": "t", "project_id": "p", "session_id": "s1",
        "message": "I prefer FastAPI backend. Never commit API keys.",
    })
    assert r1.status_code == 200
    assert r1.json()["memory_actions"]["created"]

    # Second turn: ask something; trace should include memories.
    r2 = client.post("/api/chat", json={
        "user_id": "t", "project_id": "p", "session_id": "s2",
        "message": "What backend should I use?",
    })
    body = r2.json()
    assert body["mode"] == "LOCAL_MODE"
    assert body["trace"]["candidates_considered"] >= 1
    contents = " ".join(m["content"].lower() for m in body["used_memories"])
    assert "fastapi" in contents or "api keys" in contents


def test_secret_is_redacted(client):
    captured = {}
    client.app.state.oss.put_snapshot = lambda _name, payload: captured.update(payload)
    r = client.post("/api/chat", json={
        "user_id": "t2", "project_id": "p", "session_id": "s1",
        "message": "My key is sk-abcdef0123456789abcdef0123456789 and I prefer FastAPI.",
    })
    body = r.json()
    # No stored memory should contain the raw secret.
    for m in body["memory_actions"]["created"]:
        assert "sk-abcdef0123456789" not in m["content"]
    assert "sk-abcdef0123456789" not in captured["message"]
    trace = client.app.state.last_traces["s1"]
    assert "sk-abcdef0123456789" not in trace["query"]


def test_manual_metadata_with_a_secret_is_rejected(client):
    r = client.post("/api/memories", json={
        "user_id": "t", "project_id": "p", "type": "preference",
        "content": "Use FastAPI.",
        "summary": "token=abcdef0123456789",
    })
    assert r.status_code == 400


def test_editing_content_refreshes_its_embedding(client):
    calls = []

    async def fake_embed(text):
        calls.append(text)
        return [float(len(text))]

    client.app.state.memos.qwen.embed = fake_embed
    created = client.post("/api/memories", json={
        "user_id": "t", "project_id": "p", "type": "preference",
        "content": "Use FastAPI.",
    })
    assert created.status_code == 200
    calls.clear()

    updated = client.patch(
        f"/api/memories/{created.json()['memory_id']}",
        json={"content": "Use Next.js."},
    )
    assert updated.status_code == 200
    assert calls == ["Use Next.js."]


def test_eval_runs(client):
    r = client.post("/api/eval/run")
    assert r.status_code == 200
    report = r.json()
    assert "memory_agent_accuracy" in report
    assert report["memory_agent_accuracy"] >= report["baseline_no_memory_accuracy"]
