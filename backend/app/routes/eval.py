"""Evaluation endpoints: run the benchmark and fetch the latest report."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..eval.ablation import AblationRunner
from ..eval.benchmark import BenchmarkRunner

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


@router.post("/run")
async def run_eval(request: Request):
    memos = request.app.state.memos
    runner = BenchmarkRunner(memos)
    report = await runner.run()
    request.app.state.last_eval_report = report

    # Persist the report (OSS in cloud mode, local snapshot otherwise).
    try:
        request.app.state.oss.put_snapshot("eval-reports", report)
    except Exception:  # pragma: no cover
        pass
    return report


@router.post("/ablation")
async def run_ablation(request: Request):
    """Run the governance ablation study (deterministic; isolates each mechanism)."""
    memos = request.app.state.memos
    report = await AblationRunner(memos).run()
    try:
        request.app.state.oss.put_snapshot("ablation-reports", report)
    except Exception:  # pragma: no cover
        pass
    return report


@router.get("/report")
async def eval_report(request: Request):
    report = getattr(request.app.state, "last_eval_report", None)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation report yet. POST /api/eval/run first.",
        )
    return report
