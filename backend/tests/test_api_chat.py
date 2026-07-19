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
    assert body["qwen_provider_status"] == "offline"
    assert body["qwen_fallback_used"] is False
    assert body["trace"]["candidates_considered"] >= 1
    contents = " ".join(m["content"].lower() for m in body["used_memories"])
    assert "fastapi" in contents or "api keys" in contents


def test_explicit_memory_request_uses_fallback_when_model_returns_empty(client):
    async def empty_extraction(*_args, **_kwargs):
        return {"new_memories": [], "updates": [], "forget": []}

    client.app.state.memos.qwen.extract_json = empty_extraction

    created = client.post("/api/chat", json={
        "user_id": "t", "project_id": "p", "session_id": "s1",
        "message": "Remember this for later: my deployment verification code is MP-ALIBABA-2026.",
    })
    assert created.status_code == 200
    assert created.json()["memory_actions"]["created"]

    recalled = client.post("/api/chat", json={
        "user_id": "t", "project_id": "p", "session_id": "s2",
        "message": "What is my deployment verification code?",
    })
    assert recalled.status_code == 200
    assert recalled.json()["trace"]["candidates_considered"] >= 1
    assert any(
        "mp-alibaba-2026" in memory["content"].lower()
        for memory in recalled.json()["used_memories"]
    )


def test_chat_skips_unrelated_same_project_memories(client):
    from app.memory.scorer import score_memory
    from app.models import MemoryRecord, MemoryType

    memories = [
        MemoryRecord(
            user_id="t",
            project_id="qwen-memoryagent",
            session_id="s1",
            type=MemoryType.decision,
            content="User's final demo label is CLOUD-PROOF-2026.",
            importance=0.8,
        ),
        MemoryRecord(
            user_id="t",
            project_id="qwen-memoryagent",
            session_id="s1",
            type=MemoryType.project,
            content="MemoPilot uses Alibaba Tablestore for persistent memory.",
            importance=0.9,
        ),
    ]
    similarities = [0.57, 0.42]
    scored = []
    for memory, similarity in zip(memories, similarities):
        components = score_memory(memory, similarity, "qwen-memoryagent")
        components["dense_similarity"] = similarity
        components["keyword_overlap"] = 0.0
        scored.append((memory, components))

    async def fixed_retrieval(*_args, **_kwargs):
        return scored, len(scored), 1.0

    captured = {}

    async def capture_chat(messages):
        captured["system"] = messages[0]["content"]
        return "The submitted build uses React 18 with Vite."

    async def no_memories(*_args, **_kwargs):
        return {"new_memories": [], "updates": [], "forget": []}

    client.app.state.memos.retriever.retrieve = fixed_retrieval
    client.app.state.memos.qwen.chat = capture_chat
    client.app.state.memos.qwen.extract_json = no_memories

    response = client.post("/api/chat", json={
        "user_id": "t",
        "project_id": "qwen-memoryagent",
        "session_id": "s2",
        "message": "Which frontend does this submitted build use?",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["used_memories"] == []
    assert len(body["trace"]["included"]) == 0
    assert len(body["trace"]["skipped"]) == 2
    assert "Next.js" not in captured["system"]


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
    from app.utils.identity import trace_key

    trace = client.app.state.last_traces[trace_key("t2", "s1")]
    assert "sk-abcdef0123456789" not in trace["query"]


def test_trace_is_namespaced_by_user(client):
    for user, message in (("alice", "I prefer FastAPI."), ("bob", "I prefer Django.")):
        response = client.post("/api/chat", json={
            "user_id": user,
            "project_id": "p",
            "session_id": "shared-session",
            "message": message,
        })
        assert response.status_code == 200

    alice = client.get("/api/trace/shared-session", params={"user_id": "alice"})
    bob = client.get("/api/trace/shared-session", params={"user_id": "bob"})
    assert alice.status_code == bob.status_code == 200
    assert alice.json()["user_id"] == "alice"
    assert bob.json()["user_id"] == "bob"
    assert alice.json()["query"] != bob.json()["query"]


def test_trace_cache_is_bounded(client):
    client.app.state.last_traces = {
        f"old-{index}": {"session_id": str(index)} for index in range(500)
    }

    response = client.post("/api/chat", json={
        "user_id": "trace-user",
        "project_id": "p",
        "session_id": "latest",
        "message": "I prefer FastAPI.",
    })

    assert response.status_code == 200
    assert len(client.app.state.last_traces) == 500
    assert "old-0" not in client.app.state.last_traces


def test_judge_demo_does_not_clear_default_project(client):
    created = client.post("/api/memories", json={
        "user_id": "demo-user",
        "project_id": "qwen-memoryagent",
        "type": "critical",
        "content": "Keep this real project memory.",
    })
    assert created.status_code == 200

    demo = client.post("/api/demo/run")
    assert demo.status_code == 200
    assert demo.json()["project_id"] == "qwen-memoryagent-judge-demo"

    remaining = client.get("/api/memories", params={
        "user_id": "demo-user",
        "project_id": "qwen-memoryagent",
        "include_all": True,
    }).json()
    assert any(m["content"] == "Keep this real project memory." for m in remaining["memories"])


def test_judge_demo_marks_the_migration_as_a_future_plan(client):
    demo = client.post("/api/demo/run")
    assert demo.status_code == 200
    turns = demo.json()["turns"]
    assert turns[2]["actions"]["superseded"] >= 1
    final_turn = turns[-1]
    assert final_turn["actions"]["superseded"] == 0
    assert "current React + Vite implementation" in final_turn["expectation"]


def test_judge_demo_never_calls_a_model_provider(client):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("The deterministic judge demo must not call Qwen.")

    client.app.state.memos.qwen.chat = fail_if_called
    client.app.state.memos.qwen.extract_json = fail_if_called
    client.app.state.memos.qwen.embed = fail_if_called
    client.app.state.memos.qwen.embed_many = fail_if_called
    demo = client.post("/api/demo/run")

    assert demo.status_code == 200
    turns = demo.json()["turns"]
    assert turns[2]["actions"]["superseded"] == 1
    assert "React 18 with Vite today" in turns[-1]["answer"]
    assert "planned migration" in turns[-1]["answer"]


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
        params={"user_id": "t"},
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
    assert report["primary_backbone"] == "Offline fallback"
    assert report["provider_status"] == "offline"
    assert report["provider_fallbacks"] == 0
    assert report["duration_seconds"] >= 0
    assert report["memory_token_budget"] == 2500
    assert report["outdated_memory_errors"] == 0


def test_evaluation_report_file_round_trip(tmp_path):
    from app.routes.eval import load_persisted_report, persist_report

    path = tmp_path / "latest-eval.json"
    report = {
        "generated_at": "2030-01-01T00:00:00+00:00",
        "build_sha": "abc123",
        "evaluator": "test-evaluator",
        "scenarios": [],
    }

    persist_report(str(path), report)

    assert load_persisted_report(str(path)) == report
    assert load_persisted_report(str(tmp_path / "missing.json")) is None
