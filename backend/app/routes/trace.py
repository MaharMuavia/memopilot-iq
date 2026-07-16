"""Memory trace endpoint.

Returns the most recent Memory Trace for a session — the full explanation of
which memories were retrieved, injected, or skipped, with scores, reasons, and
token-budget accounting.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..utils.identity import effective_user_id

router = APIRouter(prefix="/api", tags=["trace"])


@router.get("/trace/{session_id}")
async def get_trace(session_id: str, request: Request):
    traces = getattr(request.app.state, "last_traces", {}) or {}
    record = traces.get(session_id)
    user_id = effective_user_id(request, "")
    if record is None or (user_id and record.get("user_id") != user_id):
        raise HTTPException(
            status_code=404,
            detail=f"No trace for session '{session_id}' yet. Send a chat message first.",
        )
    return record
