"""Memory trace endpoint.

Returns the most recent Memory Trace for a session — the full explanation of
which memories were retrieved, injected, or skipped, with scores, reasons, and
token-budget accounting.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..utils.identity import effective_user_id, trace_key

router = APIRouter(prefix="/api", tags=["trace"])


@router.get("/trace/{session_id}")
async def get_trace(
    session_id: str,
    request: Request,
    user_id: str = "demo-user",
):
    traces = getattr(request.app.state, "last_traces", {}) or {}
    user_id = effective_user_id(request, user_id)
    record = traces.get(trace_key(user_id, session_id))
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No trace for session '{session_id}' yet. Send a chat message first.",
        )
    return record
