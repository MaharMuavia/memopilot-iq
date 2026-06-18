"""Hybrid memory retriever.

Combines:
  * semantic vector search (cosine similarity over embeddings)
  * keyword / tag overlap
  * structured filters (user_id, project_id, status)
  * priority boost for critical / pinned memories

Returns scored candidates (using :mod:`scorer`) ready for the ContextBuilder.
Superseded / expired / deleted / archived memories are excluded from normal
retrieval (they can only be inspected via the memory history endpoints).
"""
from __future__ import annotations

import re
import time
from typing import List, Optional, Tuple

from ..models import MemoryRecord, MemoryStatus
from .embeddings import cosine_similarity
from .scorer import score_memory

_EXCLUDED_STATES = {
    MemoryStatus.superseded,
    MemoryStatus.expired,
    MemoryStatus.deleted,
    MemoryStatus.archived,
}


def _keyword_overlap(query: str, memory: MemoryRecord) -> float:
    q = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not q:
        return 0.0
    text = f"{memory.content} {' '.join(memory.tags)}".lower()
    t = set(re.findall(r"[a-z0-9]+", text))
    if not t:
        return 0.0
    return len(q & t) / len(q)


class HybridRetriever:
    def __init__(self, store) -> None:
        self.store = store

    async def retrieve(
        self,
        user_id: str,
        project_id: Optional[str],
        query: str,
        query_embedding: List[float],
        top_k: int = 8,
    ) -> Tuple[List[Tuple[MemoryRecord, dict]], int, float]:
        """Return ``(scored, candidates_considered, latency_ms)``.

        ``scored`` is a list of ``(memory, components)`` sorted by final score.
        """
        start = time.perf_counter()
        memories = await self.store.list(user_id, project_id)
        candidates = [m for m in memories if m.status not in _EXCLUDED_STATES]

        scored: List[Tuple[MemoryRecord, dict]] = []
        for mem in candidates:
            # Hybrid similarity: blend dense vector + sparse keyword overlap.
            dense = cosine_similarity(query_embedding, mem.embedding)
            sparse = _keyword_overlap(query, mem)
            similarity = max(dense, 0.5 * dense + 0.5 * sparse)
            components = score_memory(mem, similarity, project_id)
            scored.append((mem, components))

        # Critical / pinned always sort first, then by final score.
        def sort_key(item: Tuple[MemoryRecord, dict]):
            mem, comp = item
            priority = 1 if (mem.is_critical or mem.status == MemoryStatus.pinned) else 0
            return (priority, comp["final_score"])

        scored.sort(key=sort_key, reverse=True)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return scored[: max(top_k * 2, top_k)], len(candidates), latency_ms
