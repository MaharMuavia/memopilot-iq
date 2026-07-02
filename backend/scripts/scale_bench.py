"""Scalability benchmark for the MemoryOS retrieval path.

Synthesizes N memories with random unit embeddings (matching the offline
embedding dimension) directly in memory, then times the full hybrid
retrieve -> score -> rank pass. Run from backend/:

    python scripts/scale_bench.py

Deterministic, offline, no credentials. Results are printed as a table and are
referenced in docs/evaluation_results.md.
"""
from __future__ import annotations

import asyncio
import os
import random
import statistics
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.memory.retriever import HybridRetriever  # noqa: E402
from app.models import MemoryRecord, MemoryType  # noqa: E402
from app.qwen_client import EMBED_DIM  # noqa: E402

STORE_SIZES = [1_000, 10_000, 50_000, 100_000]
QUERIES_PER_SIZE = 10
TOPICS = ["fastapi backend", "react frontend", "alibaba deployment",
          "testing strategy", "database schema", "token budget", "api design"]


class InMemoryStore:
    """Minimal store exposing only what HybridRetriever needs."""

    def __init__(self, records):
        self._records = records

    async def list(self, user_id, project_id=None, statuses=None, include_all=False):
        return self._records


def synth(n: int) -> list[MemoryRecord]:
    rng = random.Random(42)
    out = []
    for i in range(n):
        vec = [rng.gauss(0, 1) for _ in range(EMBED_DIM)]
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        out.append(MemoryRecord(
            user_id="bench", project_id="bench", session_id="s",
            type=MemoryType.preference,
            content=f"synthetic memory {i} about {TOPICS[i % len(TOPICS)]}",
            embedding=[v / norm for v in vec],
            importance=rng.random(), confidence=rng.random(),
        ))
    return out


async def main() -> None:
    try:
        import numpy  # noqa: F401
        backend = f"numpy {numpy.__version__}"
    except ImportError:
        backend = "pure python"
    print(f"vector backend: {backend} | dim={EMBED_DIM} | top_k=8")
    print(f"{'store size':>12} {'mean ms':>10} {'p95 ms':>10}")

    rng = random.Random(7)
    for n in STORE_SIZES:
        retriever = HybridRetriever(InMemoryStore(synth(n)))
        times = []
        for q in range(QUERIES_PER_SIZE):
            qvec = [rng.gauss(0, 1) for _ in range(EMBED_DIM)]
            qnorm = sum(v * v for v in qvec) ** 0.5 or 1.0
            qvec = [v / qnorm for v in qvec]
            t0 = time.perf_counter()
            await retriever.retrieve("bench", "bench", TOPICS[q % len(TOPICS)], qvec)
            times.append((time.perf_counter() - t0) * 1000.0)
        mean = statistics.mean(times)
        p95 = sorted(times)[max(0, int(len(times) * 0.95) - 1)]
        print(f"{n:>12,} {mean:>10.1f} {p95:>10.1f}")


if __name__ == "__main__":
    asyncio.run(main())
