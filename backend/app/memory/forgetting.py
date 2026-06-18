"""Forgetting engine.

Intelligent, non-destructive forgetting:
  * Expire deadline/temporary memories once ``expires_at`` passes.
  * Archive unused, low-importance memories after N days.
  * Never hard-delete user data unless the user explicitly asks (handled in the
    memories route). State transitions are recorded on the timeline.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models import MemoryRecord, MemoryStatus
from ..utils.logging import get_logger

logger = get_logger("forgetting")

ARCHIVE_AFTER_DAYS = 30
ARCHIVE_IMPORTANCE_THRESHOLD = 0.35


class ForgettingEngine:
    def __init__(self, store) -> None:
        self.store = store

    async def sweep(
        self, user_id: str, project_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Run all forgetting rules. Returns the list of changes applied."""
        now = datetime.now(timezone.utc)
        changes: List[Dict[str, str]] = []
        memories = await self.store.list(user_id, project_id, include_all=True)

        for mem in memories:
            if mem.status in {MemoryStatus.deleted, MemoryStatus.superseded}:
                continue

            # 1. Expire deadlines / temporary memories whose time has passed.
            if mem.expires_at is not None:
                exp = mem.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now and mem.status != MemoryStatus.expired:
                    await self._transition(mem, MemoryStatus.expired,
                                           "Expired: deadline/temporary lifetime passed.", changes)
                    continue

            # 2. Archive stale, unused, low-importance memories.
            if mem.status == MemoryStatus.active and not mem.is_critical:
                age_days = (now - _aware(mem.updated_at)).total_seconds() / 86400.0
                if (
                    age_days > ARCHIVE_AFTER_DAYS
                    and mem.usage_count == 0
                    and mem.importance < ARCHIVE_IMPORTANCE_THRESHOLD
                ):
                    await self._transition(mem, MemoryStatus.archived,
                                           "Archived: unused and low importance for 30+ days.", changes)

        return changes

    async def _transition(
        self,
        mem: MemoryRecord,
        new_status: MemoryStatus,
        reason: str,
        changes: List[Dict[str, str]],
    ) -> None:
        mem.status = new_status
        mem.reason = reason
        mem.updated_at = datetime.now(timezone.utc)
        await self.store.update(mem)
        await self.store.add_event(
            {
                "user_id": mem.user_id,
                "project_id": mem.project_id,
                "kind": new_status.value,
                "memory_id": mem.memory_id,
                "type": mem.type.value,
                "content": mem.content,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        changes.append({"memory_id": mem.memory_id, "new_status": new_status.value, "reason": reason})
        logger.info("Forgetting: %s -> %s (%s)", mem.memory_id, new_status.value, reason)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
