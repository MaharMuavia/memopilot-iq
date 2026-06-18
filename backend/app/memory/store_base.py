"""Abstract memory store interface.

Both the local (SQLite + in-process vectors) and Alibaba Cloud (Tablestore)
stores implement this interface, so the rest of MemoryOS is storage-agnostic.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

from ..models import MemoryRecord


class MemoryStore(abc.ABC):
    """Persistence contract for memories and the memory timeline."""

    @abc.abstractmethod
    async def init(self) -> None: ...

    @abc.abstractmethod
    async def add(self, memory: MemoryRecord) -> MemoryRecord: ...

    @abc.abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryRecord]: ...

    @abc.abstractmethod
    async def update(self, memory: MemoryRecord) -> MemoryRecord: ...

    @abc.abstractmethod
    async def delete(self, memory_id: str) -> None: ...

    @abc.abstractmethod
    async def list(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        include_all: bool = False,
    ) -> List[MemoryRecord]: ...

    @abc.abstractmethod
    async def add_event(self, event: Dict[str, Any]) -> None: ...

    @abc.abstractmethod
    async def list_events(
        self, user_id: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    async def clear_user(self, user_id: str, project_id: Optional[str] = None) -> int: ...

    @property
    @abc.abstractmethod
    def backend_name(self) -> str: ...
