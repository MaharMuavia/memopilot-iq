"""Supersession engine.

Detects when a newly extracted memory contradicts an existing active memory on
the same decision dimension (topic group) and should supersede it. Critical
memories are never auto-superseded.
"""
from __future__ import annotations

from typing import List

from ..models import MemoryRecord, MemoryStatus
from .classifier import topic_of


def find_contradictions(
    existing: List[MemoryRecord], record: MemoryRecord
) -> List[MemoryRecord]:
    """Return active memories that the new ``record`` should supersede."""
    new_topic = topic_of(record.content)
    if not new_topic:
        return []
    topic, new_member = new_topic
    out: List[MemoryRecord] = []
    for mem in existing:
        if mem.status not in {MemoryStatus.active, MemoryStatus.pinned}:
            continue
        if mem.is_critical:
            continue  # never auto-supersede critical memories
        old_topic = topic_of(mem.content)
        if old_topic and old_topic[0] == topic and old_topic[1] != new_member:
            # Same decision dimension, different choice => contradiction.
            out.append(mem)
    return out
