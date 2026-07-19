"""Deterministic memory consolidation engine.

Over the active memory set it:

  1. Merges near-duplicate memories of the same type (keeps the strongest,
     archives the rest) — reducing clutter.
  2. Promotes frequently-used memories by raising their importance.
  3. Creates explicit cluster summaries (for example, "you have 4 active
     preference memories") with the source memory IDs attached to the report.

Everything is non-destructive (merged memories are archived, not deleted) and
emits timeline events, so reflection is fully auditable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from ..models import MemoryRecord, MemoryStatus, MemoryType
from ..utils.logging import get_logger

logger = get_logger("reflection")

MERGE_SIMILARITY = 0.82
PROMOTE_USAGE_THRESHOLD = 2
SUMMARY_CLUSTER_MIN = 3
SUMMARY_TAG = "consolidation-summary"
_LEGACY_SUMMARY_TAG = "insight"


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class ReflectionEngine:
    def __init__(self, store, qwen=None) -> None:
        self.store = store
        self.qwen = qwen

    async def reflect(
        self, user_id: str, project_id: Optional[str]
    ) -> Dict[str, Any]:
        memories = await self.store.list(
            user_id, project_id,
            statuses=[MemoryStatus.active.value, MemoryStatus.pinned.value],
        )

        merged = await self._merge_duplicates(memories)
        promoted = await self._promote_used(memories)
        summaries = await self._derive_summaries(user_id, project_id, memories)

        report = {
            "reviewed": len(memories),
            "merged": merged,
            "promoted": promoted,
            "summaries": summaries,
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(
            "Consolidation: reviewed=%d merged=%d promoted=%d summaries=%d",
            len(memories), len(merged), len(promoted), len(summaries),
        )
        return report

    async def _merge_duplicates(
        self, memories: List[MemoryRecord]
    ) -> List[Dict[str, str]]:
        merged: List[Dict[str, str]] = []
        seen: List[MemoryRecord] = []
        for mem in sorted(memories, key=lambda m: m.importance, reverse=True):
            if mem.status not in {MemoryStatus.active, MemoryStatus.pinned}:
                continue
            if SUMMARY_TAG in mem.tags or _LEGACY_SUMMARY_TAG in mem.tags:
                continue
            duplicate_of = None
            for keeper in seen:
                if (
                    keeper.type == mem.type
                    and not mem.is_critical
                    and _similar(keeper.content, mem.content) >= MERGE_SIMILARITY
                ):
                    duplicate_of = keeper
                    break
            if duplicate_of is not None:
                mem.status = MemoryStatus.archived
                mem.reason = f"Merged into {duplicate_of.memory_id} during reflection."
                mem.updated_at = datetime.now(timezone.utc)
                duplicate_of.importance = min(1.0, duplicate_of.importance + 0.05)
                duplicate_of.usage_count += mem.usage_count
                await self.store.update(mem)
                await self.store.update(duplicate_of)
                await self._event(mem, "archived", mem.reason)
                merged.append({"memory_id": mem.memory_id, "into": duplicate_of.memory_id})
            else:
                seen.append(mem)
        return merged

    async def _promote_used(
        self, memories: List[MemoryRecord]
    ) -> List[Dict[str, Any]]:
        promoted: List[Dict[str, Any]] = []
        for mem in memories:
            if mem.status != MemoryStatus.active:
                continue
            if mem.usage_count >= PROMOTE_USAGE_THRESHOLD and mem.importance < 0.95:
                old = mem.importance
                mem.importance = min(1.0, round(mem.importance + 0.1, 3))
                mem.reason = (
                    f"Importance promoted {old:.2f}→{mem.importance:.2f} "
                    f"(used {mem.usage_count}×) during reflection."
                )
                mem.updated_at = datetime.now(timezone.utc)
                await self.store.update(mem)
                await self._event(mem, "updated", mem.reason)
                promoted.append(
                    {"memory_id": mem.memory_id, "from": old, "to": mem.importance}
                )
        return promoted

    async def _derive_summaries(
        self,
        user_id: str,
        project_id: Optional[str],
        memories: List[MemoryRecord],
    ) -> List[Dict[str, Any]]:
        # Cluster active memories by type. These are deterministic aggregation
        # summaries, not claims of model-derived reasoning.
        clusters: Dict[MemoryType, List[MemoryRecord]] = {}
        for mem in memories:
            if mem.status not in {MemoryStatus.active, MemoryStatus.pinned}:
                continue
            if SUMMARY_TAG in mem.tags or _LEGACY_SUMMARY_TAG in mem.tags:
                continue
            clusters.setdefault(mem.type, []).append(mem)

        existing_summaries = {
            m.summary
            for m in memories
            if SUMMARY_TAG in m.tags or _LEGACY_SUMMARY_TAG in m.tags
        }
        summaries: List[Dict[str, Any]] = []
        for mtype, group in clusters.items():
            if len(group) < SUMMARY_CLUSTER_MIN:
                continue
            label = mtype.value.replace("_", " ")
            summary = f"You have {len(group)} active {label} memories guiding this project."
            if summary in existing_summaries:
                continue
            tags = sorted({t for m in group for t in m.tags})[:6] + [SUMMARY_TAG, mtype.value]
            cluster_summary = MemoryRecord(
                user_id=user_id,
                project_id=project_id,
                session_id="consolidation",
                type=MemoryType.decision,
                status=MemoryStatus.active,
                content=summary,
                summary=summary,
                importance=0.6,
                confidence=0.8,
                tags=tags,
                reason="Deterministic count summary created by memory consolidation.",
            )
            if self.qwen is not None:
                cluster_summary.embedding = await self.qwen.embed(cluster_summary.content)
            await self.store.add(cluster_summary)
            await self._event(cluster_summary, "created", cluster_summary.reason)
            summaries.append({
                "memory_id": cluster_summary.memory_id,
                "summary": summary,
                "source_memory_ids": [memory.memory_id for memory in group],
            })
        return summaries

    async def _event(self, mem: MemoryRecord, kind: str, reason: str) -> None:
        await self.store.add_event(
            {
                "user_id": mem.user_id,
                "project_id": mem.project_id,
                "kind": kind,
                "memory_id": mem.memory_id,
                "type": mem.type.value,
                "content": mem.content,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
