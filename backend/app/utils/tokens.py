"""Token estimation utilities.

A lightweight ~4-chars-per-token heuristic — accurate enough for budgeting the
memory context window without pulling in a tokenizer dependency.
"""
from __future__ import annotations


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def count_tokens(text: str) -> int:
    """Alias for :func:`approx_tokens` with a clearer name at call sites."""
    return approx_tokens(text)
