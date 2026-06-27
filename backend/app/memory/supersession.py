"""Supersession engine.

Detects when a newly extracted memory contradicts an existing active memory on
the same decision dimension (topic group) and should supersede it. Critical
memories are never auto-superseded.

The new choice is identified in a phrasing-robust way: when a message mentions
two members of the same group (e.g. "switch from Flask to FastAPI" or "use
Next.js instead of React"), the member preceded by a replacement cue
("instead of", "from", "rather than", ...) is treated as the *old* choice, and
the remaining member as the *new* choice. This is far more reliable than a
naive first-mention rule once a live LLM rephrases the user's message.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ..models import MemoryRecord, MemoryStatus
from .classifier import TOPIC_GROUPS

# Cues that, when they appear just before a member, mark it as the OLD choice.
_REPLACE_CUES = (
    "instead of", "rather than", "switch from", "switch off", "from ",
    "no longer", "away from", "replace ", "migrate from",
)


def chosen_member(text: str) -> Optional[Tuple[str, str]]:
    """Return ``(topic_group, new_member)`` for the user's *current* choice."""
    low = text.lower()
    best: Optional[Tuple[str, str]] = None
    best_has_switch = False
    for group, members in TOPIC_GROUPS.items():
        hits = [(m, low.find(m)) for m in members if m in low]
        if not hits:
            continue
        old = set()
        for m, idx in hits:
            prefix = low[max(0, idx - 14):idx]
            if any(cue in prefix for cue in _REPLACE_CUES):
                old.add(m)
        candidates = [(m, idx) for m, idx in hits if m not in old]
        chosen = (min(candidates, key=lambda x: x[1])[0]
                  if candidates else min(hits, key=lambda x: x[1])[0])
        has_switch = bool(old)
        # Prefer a group that shows an explicit switch (old + new both present).
        if best is None or (has_switch and not best_has_switch):
            best = (group, chosen)
            best_has_switch = has_switch
    return best


def find_contradictions(
    existing: List[MemoryRecord], record: MemoryRecord
) -> List[MemoryRecord]:
    """Return active memories that the new ``record`` should supersede."""
    new_topic = chosen_member(record.content)
    if not new_topic:
        return []
    group, new_member = new_topic
    members = TOPIC_GROUPS[group]
    out: List[MemoryRecord] = []
    for mem in existing:
        if mem.status not in {MemoryStatus.active, MemoryStatus.pinned}:
            continue
        if mem.is_critical:
            continue  # never auto-supersede critical memories
        low = mem.content.lower()
        # The old memory belongs to the same group but names a different member.
        mem_member = next((m for m in members if m in low), None)
        if mem_member and mem_member != new_member:
            out.append(mem)
    return out
