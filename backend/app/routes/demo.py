"""Scripted judge-demo endpoint.

POST /api/demo/run replays the four-session MemoryAgent scenario end-to-end on
a fresh project and returns, for every turn: the message, the answer, the
memory actions (created / superseded / forgotten), the memories injected, and
the trace accounting. This is the single clearest proof of persistent memory,
cross-session recall, supersession, critical pinning, and context budgeting.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Request

from ..utils.identity import effective_user_id

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_USER = "demo-user"
DEMO_PROJECT = "qwen-memoryagent"

JUDGE_SCRIPT = [
    (
        "session-001",
        "I am building a Qwen Hackathon Track 1 MemoryAgent project. I prefer "
        "FastAPI backend, React + Vite frontend, Alibaba Cloud deployment, clean "
        "light UI, and short practical answers. Never commit API keys.",
        "Creates memories: project, preferences, and a critical safety rule.",
    ),
    (
        "session-002",
        "Design the backend architecture.",
        "New session — recalls preferences (FastAPI, Alibaba Cloud) from memory.",
    ),
    (
        "session-003",
        "Actually, use Next.js instead of React + Vite.",
        "Supersedes the React + Vite memory; Next.js becomes active.",
    ),
    (
        "session-004",
        "What stack should I use now and what should I show judges?",
        "Uses Next.js (not superseded React + Vite); critical rule still pinned.",
    ),
]


@router.post("/run")
async def run_demo(request: Request) -> Dict[str, Any]:
    memos = request.app.state.memos
    user_id = effective_user_id(request, DEMO_USER)

    # Start clean so the demo is reproducible.
    await memos.store.clear_user(user_id, DEMO_PROJECT)

    traces = getattr(request.app.state, "last_traces", None)
    if traces is None:
        traces = {}
        request.app.state.last_traces = traces

    turns: List[Dict[str, Any]] = []
    for session_id, message, expectation in JUDGE_SCRIPT:
        system_prompt, trace, used = await memos.build_context(
            user_id, DEMO_PROJECT, message
        )
        answer = await memos.qwen.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]
        )
        actions = await memos.remember(
            user_id=user_id,
            project_id=DEMO_PROJECT,
            session_id=session_id,
            message=message,
        )
        traces[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": DEMO_PROJECT,
            "query": message,
            "answer": answer,
            "trace": trace.model_dump(),
            "memory_actions": actions.model_dump(),
        }
        turns.append(
            {
                "session_id": session_id,
                "message": message,
                "expectation": expectation,
                "answer": answer,
                "injected_memories": [
                    {"content": m.content, "type": m.type.value, "is_critical": m.is_critical}
                    for m in used
                ],
                "actions": {
                    "created": len(actions.created),
                    "superseded": len(actions.superseded),
                    "forgotten": len(actions.forgotten),
                    "redacted": len(actions.redacted),
                    "superseded_ids": actions.superseded,
                },
                "trace": {
                    "tokens_used": trace.tokens_used,
                    "token_budget": trace.token_budget,
                    "included": len(trace.included),
                    "skipped": len(trace.skipped),
                    "retrieval_latency_ms": trace.retrieval_latency_ms,
                },
            }
        )

    # Final state snapshot.
    all_mems = await memos.store.list(user_id, DEMO_PROJECT, include_all=True)
    summary = {
        "active": [m.content for m in all_mems if m.status.value in ("active", "pinned")],
        "superseded": [m.content for m in all_mems if m.status.value == "superseded"],
    }

    return {"user_id": user_id, "project_id": DEMO_PROJECT, "turns": turns, "final_state": summary}
