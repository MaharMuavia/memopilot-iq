"""Evaluation endpoints: run the benchmark and fetch the latest report."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request

from ..eval.ablation import AblationRunner
from ..eval.benchmark import BenchmarkRunner
from ..utils.platform import require_admin

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


def load_persisted_report(path: Optional[str]) -> Optional[dict[str, Any]]:
    """Load a previously verified report for read-only public presentation."""
    if not path:
        return None
    try:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    required = {"generated_at", "build_sha", "evaluator", "scenarios"}
    return report if isinstance(report, dict) and required.issubset(report) else None


def persist_report(path: Optional[str], report: dict[str, Any]) -> None:
    """Atomically persist the latest synthetic evaluation report when enabled."""
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(target)


@router.post("/run")
async def run_eval(request: Request):
    require_admin(request)
    memos = request.app.state.memos
    runner = BenchmarkRunner(memos)
    report = await runner.run()
    request.app.state.last_eval_report = report
    await asyncio.to_thread(
        persist_report,
        memos.settings.eval_report_path,
        report,
    )

    # Persist the report (OSS in cloud mode, local snapshot otherwise).
    try:
        await asyncio.to_thread(
            request.app.state.oss.put_snapshot, "eval-reports", report
        )
    except Exception:  # pragma: no cover
        pass
    return report


@router.post("/ablation")
async def run_ablation(request: Request):
    """Run the governance ablation study (deterministic; isolates each mechanism)."""
    require_admin(request)
    memos = request.app.state.memos
    report = await AblationRunner(memos).run()
    try:
        await asyncio.to_thread(
            request.app.state.oss.put_snapshot, "ablation-reports", report
        )
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
