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
