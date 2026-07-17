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
        "Full policy",
        "No priority ordering",
        "No lifecycle exclusion",
        "Similarity-only weights",
        "Uniform positive weights",
    }
    assert all("context_recall" in row for row in variants.values())
    assert all("recall_at_5" not in row for row in variants.values())
    assert variants["No lifecycle exclusion"]["leak_rate"] > variants[
        "Full policy"
    ]["leak_rate"]


@pytest.mark.asyncio
async def test_benchmark_reports_raw_metric_counts(memos):
    report = await BenchmarkRunner(memos).run()

    assert report["memory_recall_total"] > 0
    assert 0 <= report["memory_recall_hits"] <= report["memory_recall_total"]
    assert report["memory_context_tokens"] >= 0
    assert report["full_history_tokens"] > 0
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
