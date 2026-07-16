"""Tests for the production platform layer: auth, rate limiting, metrics,
pagination/filtering, and the per-memory audit history endpoint."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _make_client(tmp_path, monkeypatch, **env):
    monkeypatch.setenv("APP_MODE", "local")
    monkeypatch.setenv("MEMORY_STORE", "sqlite")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'platform.db'}")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("MEMOPILOT_API_KEYS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    from app.config import get_settings
    get_settings.cache_clear()
    from app.main import create_app
    return TestClient(create_app())


# ---------------------------------------------------------------- auth
def test_open_mode_when_no_keys_configured(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch) as c:
        assert c.get("/api/memories").status_code == 200


def test_api_key_required_when_configured(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch, MEMOPILOT_API_KEYS="mk-alpha, mk-beta") as c:
        assert c.get("/api/memories").status_code == 401
        assert c.get("/api/memories", headers={"X-API-Key": "wrong"}).status_code == 401
        assert c.get("/api/memories", headers={"X-API-Key": "mk-alpha"}).status_code == 200
        assert c.get("/api/memories", headers={"X-API-Key": "mk-beta"}).status_code == 200
        # Health and metrics stay public.
        assert c.get("/health").status_code == 200
        assert c.get("/metrics").status_code == 200


def test_api_key_owns_its_memory_namespace(tmp_path, monkeypatch):
    headers_a = {"X-API-Key": "mk-alpha"}
    headers_b = {"X-API-Key": "mk-beta"}
    with _make_client(tmp_path, monkeypatch, MEMOPILOT_API_KEYS="mk-alpha,mk-beta") as c:
        # A body-supplied user id cannot select another user's namespace once
        # API-key authentication is enabled.
        created = c.post("/api/memories", headers=headers_a, json={
            "user_id": "victim", "project_id": "p", "type": "preference",
            "content": "alpha private preference",
        })
        assert created.status_code == 200
        memory_id = created.json()["memory_id"]
        assert created.json()["user_id"] != "victim"

        assert c.get("/api/memories", headers=headers_b).json()["total"] == 0
        assert c.patch(f"/api/memories/{memory_id}", headers=headers_b,
                       json={"pin": True}).status_code == 404
        assert c.patch(f"/api/memories/{memory_id}", headers=headers_a,
                       json={"pin": True}).status_code == 200


# ---------------------------------------------------------- rate limiting
def test_rate_limit_enforced(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch, RATE_LIMIT_PER_MINUTE="5") as c:
        codes = [c.get("/api/memories").status_code for _ in range(7)]
        assert codes[:5] == [200] * 5
        assert 429 in codes[5:]


# ---------------------------------------------------------------- metrics
def test_metrics_exposition(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch) as c:
        c.get("/api/memories")
        body = c.get("/metrics").text
        assert "memopilot_requests_total" in body
        assert "memopilot_request_latency_ms_sum" in body
        assert 'route="/api/memories"' in body


# ------------------------------------------------- pagination + filtering
def test_pagination_and_filters(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch) as c:
        for i in range(12):
            r = c.post("/api/memories", json={
                "user_id": "p", "project_id": "proj", "type": "preference",
                "content": f"unique preference item number {i}",
            })
            assert r.status_code == 200
        page1 = c.get("/api/memories", params={
            "user_id": "p", "project_id": "proj", "limit": 5, "offset": 0,
        }).json()
        page2 = c.get("/api/memories", params={
            "user_id": "p", "project_id": "proj", "limit": 5, "offset": 5,
        }).json()
        assert page1["total"] == 12 and page1["count"] == 5 and page2["count"] == 5
        ids1 = {m["memory_id"] for m in page1["memories"]}
        ids2 = {m["memory_id"] for m in page2["memories"]}
        assert not ids1 & ids2  # disjoint pages

        # text search filter
        hit = c.get("/api/memories", params={
            "user_id": "p", "project_id": "proj", "q": "number 7",
        }).json()
        assert hit["total"] == 1

        # type filter mismatch yields nothing
        none = c.get("/api/memories", params={
            "user_id": "p", "project_id": "proj", "type": "deadline",
        }).json()
        assert none["total"] == 0


# --------------------------------------------------------- audit history
def test_memory_history_trail(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch) as c:
        created = c.post("/api/memories", json={
            "user_id": "h", "project_id": "proj", "type": "preference",
            "content": "history subject memory",
        }).json()
        mid = created["memory_id"]
        c.patch(f"/api/memories/{mid}", json={"pin": True})
        c.delete(f"/api/memories/{mid}")

        trail = c.get(f"/api/memories/{mid}/history",
                      params={"user_id": "h", "project_id": "proj"}).json()
        kinds = [e["kind"] for e in trail["events"]]
        assert "created" in kinds and "deleted" in kinds
        assert trail["count"] >= 3  # created + pinned + deleted
        assert trail["current"]["status"] == "deleted"

        missing = c.get("/api/memories/mem_nonexistent/history",
                        params={"user_id": "h", "project_id": "proj"})
        assert missing.status_code == 404


def test_forget_all_erases_events_as_well_as_memories(tmp_path, monkeypatch):
    with _make_client(tmp_path, monkeypatch) as c:
        created = c.post("/api/memories", json={
            "user_id": "erase", "project_id": "proj", "type": "preference",
            "content": "erase this event too",
        })
        assert created.status_code == 200
        assert c.get("/api/memories/timeline", params={
            "user_id": "erase", "project_id": "proj",
        }).json()["count"] == 1

        response = c.post("/api/memories/forget-all", params={
            "user_id": "erase", "project_id": "proj",
        })
        assert response.status_code == 200
        assert response.json()["forgotten"] == 1
        # The forget-all endpoint writes one deletion event after clearing the
        # prior audit trail; it must not retain the erased memory content.
        events = c.get("/api/memories/timeline", params={
            "user_id": "erase", "project_id": "proj",
        }).json()["events"]
        assert len(events) == 1
        assert "erase this event too" not in events[0]["content"]
