"""MemoPilot IQ Python SDK — embed MemoryOS in any agent in a few lines.

A single-file, dependency-light client (only ``requests``) for the MemoPilot IQ
backend. Vendor this file or install requests and copy it into your project.

Quickstart::

    from memopilot import MemoPilotClient

    mp = MemoPilotClient("http://localhost:8000", api_key="mk-...optional...")

    # Memory-augmented chat: answer + used memories + full trace
    r = mp.chat("What stack should I use?", user_id="alice", project_id="webapp")
    print(r["answer"])
    for m in r["used_memories"]:
        print(" recalled:", m["content"])

    # Direct memory operations
    mp.add_memory("Prefers FastAPI for backends", type="preference",
                  user_id="alice", project_id="webapp")
    page = mp.memories(user_id="alice", project_id="webapp", q="fastapi", limit=20)
    mp.pin(page["memories"][0]["memory_id"])

Auth: pass ``api_key`` when the server sets ``MEMOPILOT_API_KEYS``; it is sent
as the ``X-API-Key`` header. All methods raise :class:`MemoPilotError` on
non-2xx responses.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

__all__ = ["MemoPilotClient", "MemoPilotError"]
__version__ = "1.0.0"


class MemoPilotError(RuntimeError):
    """Raised for any non-2xx API response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class MemoPilotClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        if api_key:
            self._session.headers["X-API-Key"] = api_key

    # ------------------------------------------------------------------ core
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._session.request(
            method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs
        )
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text
            raise MemoPilotError(resp.status_code, str(detail))
        return resp.json()

    # ---------------------------------------------------------------- health
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    # ------------------------------------------------------------------ chat
    def chat(
        self,
        message: str,
        user_id: str = "demo-user",
        project_id: Optional[str] = "qwen-memoryagent",
        session_id: str = "sdk-session",
    ) -> Dict[str, Any]:
        """Memory-augmented chat. Returns answer, used_memories, actions, trace."""
        return self._request("POST", "/api/chat", json={
            "user_id": user_id, "project_id": project_id,
            "session_id": session_id, "message": message,
        })

    # -------------------------------------------------------------- memories
    def memories(
        self,
        user_id: str = "demo-user",
        project_id: Optional[str] = "qwen-memoryagent",
        include_all: bool = False,
        type: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List/search memories with filters and pagination."""
        params: Dict[str, Any] = {
            "user_id": user_id, "include_all": include_all,
            "limit": limit, "offset": offset,
        }
        if project_id is not None:
            params["project_id"] = project_id
        for k, v in (("type", type), ("status", status), ("q", q)):
            if v is not None:
                params[k] = v
        return self._request("GET", "/api/memories", params=params)

    def add_memory(
        self,
        content: str,
        type: str = "preference",
        user_id: str = "demo-user",
        project_id: Optional[str] = "qwen-memoryagent",
        importance: float = 0.6,
        is_critical: bool = False,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self._request("POST", "/api/memories", json={
            "user_id": user_id, "project_id": project_id, "type": type,
            "content": content, "importance": importance,
            "is_critical": is_critical, "tags": tags or [],
        })

    def history(
        self,
        memory_id: str,
        user_id: str = "demo-user",
        project_id: Optional[str] = "qwen-memoryagent",
    ) -> Dict[str, Any]:
        """Per-memory audit trail (every lifecycle event)."""
        return self._request(
            "GET", f"/api/memories/{memory_id}/history",
            params={"user_id": user_id, "project_id": project_id},
        )

    def pin(self, memory_id: str) -> Dict[str, Any]:
        return self._request("PATCH", f"/api/memories/{memory_id}", json={"pin": True})

    def archive(self, memory_id: str) -> Dict[str, Any]:
        return self._request("PATCH", f"/api/memories/{memory_id}", json={"archive": True})

    def forget(self, memory_id: str, hard: bool = False) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/memories/{memory_id}", params={"hard": hard})

    def forget_all(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        return self._request("POST", "/api/memories/forget-all",
                             params={"user_id": user_id, "project_id": project_id})

    def export(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        return self._request("GET", "/api/memories/export",
                             params={"user_id": user_id, "project_id": project_id})

    def timeline(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        return self._request("GET", "/api/memories/timeline",
                             params={"user_id": user_id, "project_id": project_id})

    # ------------------------------------------------------- intelligence ops
    def reflect(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        """Run the reflection/consolidation pass."""
        return self._request("POST", "/api/reflect",
                             params={"user_id": user_id, "project_id": project_id})

    def graph(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        return self._request("GET", "/api/graph",
                             params={"user_id": user_id, "project_id": project_id})

    def analytics(
        self, user_id: str = "demo-user", project_id: Optional[str] = "qwen-memoryagent"
    ) -> Dict[str, Any]:
        return self._request("GET", "/api/analytics",
                             params={"user_id": user_id, "project_id": project_id})

    # ------------------------------------------------------------- evaluation
    def run_benchmark(self) -> Dict[str, Any]:
        return self._request("POST", "/api/eval/run")

    def run_ablation(self) -> Dict[str, Any]:
        return self._request("POST", "/api/eval/ablation")

    def run_demo(self) -> Dict[str, Any]:
        return self._request("POST", "/api/demo/run")
