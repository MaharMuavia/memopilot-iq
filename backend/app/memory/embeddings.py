"""Embedding utilities and cosine similarity.

Embeddings are produced by :class:`QwenClient` (Qwen embedding endpoint when
online, deterministic hashing fallback when offline). This module only holds
the math used by the retriever.
"""
from __future__ import annotations

import math
from typing import List, Optional


def cosine_similarity(a: Optional[List[float]], b: Optional[List[float]]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    sim = dot / (na * nb)
    # Clamp to [0, 1] for scoring (negative similarity treated as 0).
    return max(0.0, min(1.0, sim))


def batch_cosine(
    query: Optional[List[float]], vectors: List[Optional[List[float]]]
) -> List[float]:
    """Cosine similarity of ``query`` against many vectors at once.

    Uses a vectorized NumPy path when available (one matrix-vector product for
    the whole store — this is what keeps exhaustive scoring in the low
    milliseconds at 10^4–10^5 memories), and falls back to the pure-Python
    loop otherwise. Vectors that are missing or of mismatched dimension score 0.
    """
    if not query:
        return [0.0] * len(vectors)
    dim = len(query)
    try:
        import numpy as np  # optional accelerator

        idx = [i for i, v in enumerate(vectors) if v and len(v) == dim]
        out = [0.0] * len(vectors)
        if idx:
            mat = np.asarray([vectors[i] for i in idx], dtype=np.float32)
            qv = np.asarray(query, dtype=np.float32)
            qn = float(np.linalg.norm(qv))
            if qn > 0.0:
                norms = np.linalg.norm(mat, axis=1)
                norms[norms == 0.0] = 1.0
                sims = (mat @ qv) / (norms * qn)
                sims = np.clip(sims, 0.0, 1.0)
                for j, i in enumerate(idx):
                    out[i] = float(sims[j])
        return out
    except ImportError:  # pragma: no cover - numpy is normally present
        return [cosine_similarity(query, v) for v in vectors]
