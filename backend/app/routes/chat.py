"""Chat endpoint — the core memory-augmented conversation loop.

Flow for each request:
  1. Build context from MemoryOS (retrieve + score + budget) -> system prompt + trace.
  2. Call Qwen with the budgeted context.
  3. Extract new memories from the user message (after answering).
  4. Snapshot the turn to OSS (or local fallback).
  5. Return answer + used memories + memory actions + trace + mode.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

from ..models import ChatRequest, ChatResponse
from ..utils.identity import effective_user_id, trace_key
from ..utils.logging import get_logger
from ..utils.security import redact_secrets

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger("chat")
_TRACE_CACHE_MAX_ENTRIES = 500


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    memos = request.app.state.memos
    oss = request.app.state.oss
    user_id = effective_user_id(request, req.user_id)

    # 1 + 2: build budgeted context and answer.
    system_prompt, trace, used = await memos.build_context(
        user_id, req.project_id, req.message
    )
    fallback_count_before = memos.qwen.fallback_count
    # The answer and memory extraction are independent after context is built;
    # running them together avoids serial provider latency on normal chat.
    answer, actions = await asyncio.gather(
        memos.qwen.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message},
            ]
        ),
        memos.remember(
            user_id=user_id,
            project_id=req.project_id,
            session_id=req.session_id,
            message=req.message,
        ),
    )

    # 4: snapshot the turn (OSS in cloud mode, local file otherwise).
    try:
        await asyncio.to_thread(
            oss.put_snapshot,
            "turns",
            {
                "user_id": user_id,
                "project_id": req.project_id,
                "session_id": req.session_id,
                "message": redact_secrets(req.message),
                "answer": redact_secrets(answer),
                "used_memory_ids": [m.memory_id for m in used],
                "memory_actions": actions.model_dump(),
            },
        )
    except Exception as exc:  # pragma: no cover - snapshot must never break chat
        logger.warning("Snapshot failed: %s", exc)

    # Persist the latest trace per session so GET /api/trace/{session_id} works.
    traces = getattr(request.app.state, "last_traces", None)
    if traces is None:
        traces = {}
        request.app.state.last_traces = traces
    traces[trace_key(user_id, req.session_id)] = {
        "session_id": req.session_id,
        "user_id": user_id,
        "project_id": req.project_id,
        # This is process-local diagnostic state, but it follows the same
        # redaction rule as durable snapshots so a later persistence change
        # cannot accidentally retain credentials.
        "query": redact_secrets(req.message),
        "answer": redact_secrets(answer),
        "trace": trace.model_dump(),
        "memory_actions": actions.model_dump(),
    }
    while len(traces) > _TRACE_CACHE_MAX_ENTRIES:
        traces.pop(next(iter(traces)))

    fallback_used = memos.qwen.fallback_count > fallback_count_before
    provider_status = (
        "degraded_offline_fallback" if fallback_used else memos.qwen.provider_status
    )
    return ChatResponse(
        answer=answer,
        used_memories=[m.public_view() for m in used],
        memory_actions=actions,
        trace=trace,
        mode=memos.mode,
        qwen_provider_status=provider_status,
        qwen_fallback_used=fallback_used,
    )
