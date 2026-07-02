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

import heapq

from ..models import MemoryRecord, MemoryStatus
from .embeddings import batch_cosine, cosine_similarity  # noqa: F401 (cosine kept for API)
from .scorer import score_memory

# Two-stage rerank kicks in above this store size; the pool is the number of
# dense-nearest candidates that receive full hybrid scoring. Critical/pinned
# records always join the pool regardless of dense rank.
_RERANK_THRESHOLD = 1024
_RERANK_POOL = 512

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

        # Stage 1 — dense similarities in one vectorized pass (NumPy when
        # available): a single matrix-vector product over the whole store.
        dense_all = batch_cosine(query_embedding, [m.embedding for m in candidates])

        # Stage 2 — full hybrid scoring (sparse overlap + interpretable score)
        # runs on everything for small stores, and on the dense top pool plus
        # every critical/pinned record for large ones (retrieve-then-rerank).
        if len(candidates) > _RERANK_THRESHOLD:
            keep = set(heapq.nlargest(
                _RERANK_POOL, range(len(candidates)), key=lambda i: dense_all[i]
            ))
            for i, mem in enumerate(candidates):
                if mem.is_critical or mem.status == MemoryStatus.pinned:
                    keep.add(i)
            pool = [(candidates[i], dense_all[i]) for i in keep]
        else:
            pool = list(zip(candidates, dense_all))

        scored: List[Tuple[MemoryRecord, dict]] = []
        for mem, dense in pool:
            # Hybrid similarity: blend dense vector + sparse keyword overlap.
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
