"""Local memory store: SQLite for metadata + in-process vectors.

This is the default LOCAL_MODE backend. It uses SQLite (via the stdlib
``sqlite3`` module, run in a thread to stay async-friendly) for durable
metadata, and keeps embedding vectors in the same row as a JSON blob. Semantic
search is performed in :mod:`retriever` using brute-force cosine similarity,
which is more than fast enough for a hackathon-scale memory store. If FAISS or
Chroma are installed they can be dropped in behind the same interface.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any, Dict, List, Optional

from ..models import MemoryRecord
from ..utils.logging import get_logger
from .store_base import MemoryStore

logger = get_logger("store_sqlite")


def _db_path_from_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "", 1)
    return url


class SQLiteMemoryStore(MemoryStore):
    def __init__(self, database_url: str = "sqlite:///./memopilot.db") -> None:
        self._path = _db_path_from_url(database_url)
        self._lock = asyncio.Lock()

    @property
    def backend_name(self) -> str:
        return "sqlite+local-vectors"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    async def init(self) -> None:
        def _create() -> None:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        memory_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        project_id TEXT,
                        data TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        project_id TEXT,
                        data TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id, project_id)"
                )
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_create)
        logger.info("SQLite memory store ready at %s", self._path)

    async def add(self, memory: MemoryRecord) -> MemoryRecord:
        def _add() -> None:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO memories(memory_id,user_id,project_id,data) VALUES(?,?,?,?)",
                    (
                        memory.memory_id,
                        memory.user_id,
                        memory.project_id,
                        memory.model_dump_json(),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        async with self._lock:
            await asyncio.to_thread(_add)
        return memory

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        def _get() -> Optional[str]:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT data FROM memories WHERE memory_id=?", (memory_id,)
                ).fetchone()
                return row["data"] if row else None
            finally:
                conn.close()

        data = await asyncio.to_thread(_get)
        return MemoryRecord.model_validate_json(data) if data else None

    async def update(self, memory: MemoryRecord) -> MemoryRecord:
        return await self.add(memory)

    async def delete(self, memory_id: str) -> None:
        def _del() -> None:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM memories WHERE memory_id=?", (memory_id,))
                conn.commit()
            finally:
                conn.close()

        async with self._lock:
            await asyncio.to_thread(_del)

    async def list(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        include_all: bool = False,
    ) -> List[MemoryRecord]:
        def _list() -> List[str]:
            conn = self._connect()
            try:
                if project_id is not None:
                    rows = conn.execute(
                        "SELECT data FROM memories WHERE user_id=? AND (project_id=? OR project_id IS NULL)",
                        (user_id, project_id),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT data FROM memories WHERE user_id=?", (user_id,)
                    ).fetchall()
                return [r["data"] for r in rows]
            finally:
                conn.close()

        raw = await asyncio.to_thread(_list)
        records = [MemoryRecord.model_validate_json(d) for d in raw]
        if include_all:
            return records
        if statuses:
            return [m for m in records if m.status.value in statuses]
        return records

    async def add_event(self, event: Dict[str, Any]) -> None:
        def _add() -> None:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO events(user_id,project_id,data) VALUES(?,?,?)",
                    (
                        event.get("user_id", ""),
                        event.get("project_id"),
                        json.dumps(event, default=str),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_add)

    async def list_events(
        self, user_id: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        def _list() -> List[str]:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT data FROM events WHERE user_id=? ORDER BY id DESC LIMIT 200",
                    (user_id,),
                ).fetchall()
                return [r["data"] for r in rows]
            finally:
                conn.close()

        raw = await asyncio.to_thread(_list)
        events = [json.loads(d) for d in raw]
        if project_id is not None:
            events = [e for e in events if e.get("project_id") in (project_id, None)]
        return events

    async def clear_user(self, user_id: str, project_id: Optional[str] = None) -> int:
        def _clear() -> int:
            conn = self._connect()
            try:
                if project_id is not None:
                    cur = conn.execute(
                        "DELETE FROM memories WHERE user_id=? AND (project_id=? OR project_id IS NULL)",
                        (user_id, project_id),
                    )
                    conn.execute(
                        "DELETE FROM events WHERE user_id=? AND (project_id=? OR project_id IS NULL)",
                        (user_id, project_id),
                    )
                else:
                    cur = conn.execute(
                        "DELETE FROM memories WHERE user_id=?", (user_id,)
                    )
                    conn.execute("DELETE FROM events WHERE user_id=?", (user_id,))
                conn.commit()
                return cur.rowcount
            finally:
                conn.close()

        async with self._lock:
            return await asyncio.to_thread(_clear)
