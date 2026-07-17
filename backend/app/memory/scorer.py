"""Memory scoring engine.

Implements the MemoPilot ranking formula. The final score combines semantic
similarity with intrinsic memory signals (importance, recency, confidence,
usage), contextual signals (project match, critical bonus) and penalties
(outdated, privacy, superseded).

    final_score =
        0.40 * semantic_similarity
      + 0.20 * importance
      + 0.15 * recency_score
      + 0.10 * confidence
      + 0.10 * usage_score
      + 0.15 * project_match
      + 0.20 * critical_bonus
      - 0.30 * outdated_penalty
      - 0.25 * privacy_penalty
      - 0.50 * superseded_penalty
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, Optional

from ..models import MemoryRecord, MemoryStatus, MemoryType, PrivacyLevel

WEIGHTS = {
    "semantic_similarity": 0.40,
    "importance": 0.20,
    "recency_score": 0.15,
    "confidence": 0.10,
    "usage_score": 0.10,
    "project_match": 0.15,
    "critical_bonus": 0.20,
    "outdated_penalty": -0.30,
    "privacy_penalty": -0.25,
    "superseded_penalty": -0.50,
}


def compute_recency(updated_at: datetime, time_constant_days: float = 14.0) -> float:
    """Exponential recency decay using the configured time constant."""
    if time_constant_days <= 0:
        raise ValueError("time_constant_days must be greater than zero")
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - updated_at).total_seconds() / 86400.0)
    return math.exp(-age_days / time_constant_days)


def usage_to_score(usage_count: int) -> float:
    """Diminishing-returns usage score in [0, 1]."""
    return 1.0 - 1.0 / (1.0 + math.log1p(max(0, usage_count)))


def score_memory(
    memory: MemoryRecord,
    semantic_similarity: float,
    current_project_id: Optional[str],
) -> Dict[str, float]:
    """Return the component breakdown and the final score for a memory."""
    recency = compute_recency(memory.updated_at)
    usage_score = usage_to_score(memory.usage_count)

    project_match = 1.0 if (
        current_project_id and memory.project_id == current_project_id
    ) else 0.0

    critical_bonus = 1.0 if (
        memory.is_critical
        or memory.status == MemoryStatus.pinned
        or memory.type == MemoryType.critical
    ) else 0.0

    outdated_penalty = 1.0 if (
        memory.type == MemoryType.outdated or memory.status == MemoryStatus.archived
    ) else 0.0

    privacy_penalty = {
        PrivacyLevel.public: 0.0,
        PrivacyLevel.private: 0.4,
        PrivacyLevel.sensitive: 1.0,
    }[memory.privacy_level]

    superseded_penalty = 1.0 if memory.status in {
        MemoryStatus.superseded,
        MemoryStatus.expired,
        MemoryStatus.deleted,
    } else 0.0

    components = {
        "semantic_similarity": semantic_similarity,
        "importance": memory.importance,
        "recency_score": recency,
        "confidence": memory.confidence,
        "usage_score": usage_score,
        "project_match": project_match,
        "critical_bonus": critical_bonus,
        "outdated_penalty": outdated_penalty,
        "privacy_penalty": privacy_penalty,
        "superseded_penalty": superseded_penalty,
    }

    final = sum(WEIGHTS[k] * v for k, v in components.items())
    components["final_score"] = round(final, 4)
    # Persist recency/usage we computed so callers can store them.
    components["_recency_score"] = recency
    components["_usage_score"] = usage_score
    return components
