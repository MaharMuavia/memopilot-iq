"""Tests for the memory scoring engine."""
from __future__ import annotations

from datetime import datetime, timezone

from app.memory.scorer import WEIGHTS, score_memory, compute_recency, usage_to_score
from app.models import MemoryRecord, MemoryStatus, MemoryType, PrivacyLevel


def _mem(**kwargs) -> MemoryRecord:
    base = dict(
        user_id="u",
        session_id="s",
        project_id="p",
        content="prefer fastapi",
    )
    base.update(kwargs)
    return MemoryRecord(**base)


def test_weights_match_spec():
    assert WEIGHTS["semantic_similarity"] == 0.40
    assert WEIGHTS["superseded_penalty"] == -0.50
    assert WEIGHTS["critical_bonus"] == 0.20


def test_critical_memory_scores_higher_than_plain():
    plain = _mem(importance=0.5)
    critical = _mem(importance=0.5, is_critical=True, type=MemoryType.critical)
    s_plain = score_memory(plain, 0.5, "p")["final_score"]
    s_crit = score_memory(critical, 0.5, "p")["final_score"]
    assert s_crit > s_plain


def test_superseded_memory_is_penalised():
    active = _mem()
    superseded = _mem(status=MemoryStatus.superseded)
    assert (
        score_memory(superseded, 0.8, "p")["final_score"]
        < score_memory(active, 0.8, "p")["final_score"]
    )


def test_project_match_boosts_score():
    in_proj = score_memory(_mem(project_id="p"), 0.5, "p")["final_score"]
    out_proj = score_memory(_mem(project_id="other"), 0.5, "p")["final_score"]
    assert in_proj > out_proj


def test_sensitive_privacy_penalised():
    public = score_memory(_mem(privacy_level=PrivacyLevel.public), 0.5, "p")["final_score"]
    sensitive = score_memory(_mem(privacy_level=PrivacyLevel.sensitive), 0.5, "p")["final_score"]
    assert sensitive < public


def test_recency_decays():
    now = datetime.now(timezone.utc)
    fresh = compute_recency(now)
    assert 0.99 <= fresh <= 1.0


def test_usage_score_monotonic():
    assert usage_to_score(0) < usage_to_score(5) < usage_to_score(50)
