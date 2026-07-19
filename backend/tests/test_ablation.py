"""Regression tests for the deterministic governance ablation."""
from __future__ import annotations

import pytest

from app.eval.ablation import AblationRunner
from app.eval.benchmark import BenchmarkRunner


@pytest.mark.asyncio
async def test_ablation_reports_clean_single_factor_variants(memos):
    report = await AblationRunner(memos).run()

    assert report["num_scenarios"] == 24
    assert report["retrieval_top_k"] == 8
    assert report["memory_token_budget"] == 2500

    variants = {row["variant"]: row for row in report["variants"]}
    assert set(variants) == {
        "Full conversation history",
        "Dense-only retrieval",
        "Recency-only retrieval",
        "Hybrid without lifecycle exclusion",
        "Full governance",
    }
    assert all("context_recall" in row for row in variants.values())
    assert all("avg_context_tokens" in row for row in variants.values())
    assert all("retrieval_latency_p95_ms" in row for row in variants.values())
    assert all("recall_at_5" not in row for row in variants.values())
    assert variants["Hybrid without lifecycle exclusion"]["stale_memory_leak_rate"] > variants[
        "Full governance"
    ]["stale_memory_leak_rate"]


@pytest.mark.asyncio
async def test_benchmark_reports_raw_metric_counts(memos):
    report = await BenchmarkRunner(memos).run()

    assert report["memory_recall_total"] > 0
    assert 0 <= report["memory_recall_hits"] <= report["memory_recall_total"]
    assert report["memory_context_tokens"] >= 0
    assert report["full_history_tokens"] > 0
    assert 0 <= report["baseline_full_history_accuracy"] <= 1
    assert 0 <= report["baseline_history_summary_accuracy"] <= 1
    assert report["model_calls_per_scenario_per_backbone"] == 5
    assert "totals" in report["provider_token_usage"]
    assert all("full_history_correct" in row for row in report["scenarios"])
    assert all("history_summary_correct" in row for row in report["scenarios"])
    assert report["memory_recall_at_context"] == round(
        report["memory_recall_hits"] / report["memory_recall_total"], 2
    )
    assert report["token_savings_percent"] == round(
        100
        * (
            1
            - report["memory_context_tokens"] / report["full_history_tokens"]
        )
    )
