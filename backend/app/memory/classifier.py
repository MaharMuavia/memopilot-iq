"""Memory classifier.

Owns the topic-group taxonomy used for contradiction detection and a light
type-classification helper. The extractor and supersession engine import from
here so classification logic lives in one place.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Topic groups used for lightweight contradiction detection. A new memory in
# the same group with a different member supersedes the old one (e.g. switching
# frontend framework from React + Vite to Next.js).
TOPIC_GROUPS: Dict[str, List[str]] = {
    "frontend_framework": ["react", "vite", "next.js", "nextjs", "vue", "angular", "svelte"],
    "backend_framework": ["fastapi", "flask", "django", "express", "spring"],
    "cloud_provider": ["alibaba", "aws", "azure", "gcp", "google cloud"],
    "ui_theme": ["light ui", "dark ui", "light mode", "dark mode"],
    "database": ["postgresql", "postgres", "mysql", "sqlite", "mongodb"],
    "package_manager": ["pnpm", "npm", "yarn"],
}


def topic_of(text: str) -> Optional[Tuple[str, str]]:
    """Return ``(topic_group, member)`` for the *first-mentioned* member.

    Picking the earliest member by text position matters for phrases like
    "Use Next.js instead of React + Vite": the new choice ("Next.js") appears
    before the thing being replaced, so it must win the topic assignment.
    """
    low = text.lower()
    best: Optional[Tuple[str, str]] = None
    best_idx = len(low) + 1
    for topic, members in TOPIC_GROUPS.items():
        for member in members:
            idx = low.find(member)
            if idx != -1 and idx < best_idx:
                best_idx = idx
                best = (topic, member)
    return best
