"""Reflection endpoint — runs the memory consolidation / self-improvement pass."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..utils.identity import effective_user_id

router = APIRouter(prefix="/api", tags=["reflection"])


@router.post("/reflect")
async def reflect(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    user_id = effective_user_id(request, user_id)
    report = await memos.reflection.reflect(user_id, project_id)

    # Persist the reflection report (OSS in cloud mode, local snapshot otherwise).
    try:
        request.app.state.oss.put_snapshot("reflection", report)
    except Exception:  # pragma: no cover
        pass
    return report
