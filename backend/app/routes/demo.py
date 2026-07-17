"""Reproducible judge-demo endpoint for the memory lifecycle."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request

from ..demo_runner import DEMO_USER, ScriptedDemoRunner
from ..utils.identity import effective_user_id, trace_key

router = APIRouter(prefix="/api/demo", tags=["demo"])
_TRACE_CACHE_MAX_ENTRIES = 500


@router.post("/run")
async def run_demo(request: Request) -> Dict[str, Any]:
    """Run a provider-independent, transparent lifecycle demonstration.

    This endpoint proves the memory system using its real persistence,
    retrieval, scoring, supersession, and context-budget components. The live
    Qwen conversation remains available through ``POST /api/chat``.
    """
    user_id = effective_user_id(request, DEMO_USER)
    result, traces_to_store = await ScriptedDemoRunner(
        request.app.state.memos, user_id
    ).run()

    traces = getattr(request.app.state, "last_traces", None)
    if traces is None:
        traces = {}
        request.app.state.last_traces = traces
    for trace in traces_to_store:
        traces[trace_key(user_id, trace["session_id"])] = trace
    while len(traces) > _TRACE_CACHE_MAX_ENTRIES:
        traces.pop(next(iter(traces)))

    return result
