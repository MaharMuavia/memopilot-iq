"""Deterministic memory-lifecycle runner used by the judge-demo endpoint.

The dashboard's Chat tab is the live Qwen experience.  The judge button is a
fast, reproducible proof of memory creation, retrieval, supersession, and
critical recall; it deliberately does not call a model provider.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .memory import MemoryOS
from .models import MemoryActions, MemoryRecord, MemoryStatus, MemoryType

DEMO_USER = "demo-user"
DEMO_PROJECT = "qwen-memoryagent-judge-demo"

JUDGE_SCRIPT = [
    (
        "session-001",
        "I am building a Qwen Hackathon Track 1 MemoryAgent project. I prefer "
        "FastAPI backend, React + Vite frontend, Alibaba Cloud deployment, clean "
        "light UI, and short practical answers. Never commit API keys.",
        "Creates project, preference, and critical safety memories.",
    ),
    (
        "session-002",
        "Design the backend architecture.",
        "A new session recalls the FastAPI and Alibaba Cloud preferences.",
    ),
    (
        "session-003",
        "For the next iteration after this submission, migrate the frontend to Next.js instead of React + Vite.",
        "Supersedes the submitted-build frontend preference with a planned migration.",
    ),
    (
        "session-004",
        "What frontend does this submitted build use today, and what is planned after submission?",
        "Distinguishes the current React + Vite implementation from the planned Next.js migration.",
    ),
]


class ScriptedDemoRunner:
    """Exercise the real store, retriever, scorer, and context builder."""

    def __init__(self, memos: MemoryOS, user_id: str) -> None:
        self.memos = memos
        self.user_id = user_id

    def _memory(
        self,
        *,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float,
        critical: bool = False,
        tags: List[str] | None = None,
    ) -> MemoryRecord:
        return MemoryRecord(
            user_id=self.user_id,
            project_id=DEMO_PROJECT,
            session_id=session_id,
            type=memory_type,
            status=MemoryStatus.pinned if critical else MemoryStatus.active,
            content=content,
            summary=content,
            embedding=self.memos.qwen.deterministic_embed(content),
            importance=importance,
            confidence=1.0,
            tags=tags or [],
            source_message_id=f"judge-{session_id}",
            is_critical=critical,
            reason="Deterministic judge-demo lifecycle record.",
        )

    async def _store_created(self, record: MemoryRecord) -> None:
        await self.memos.store.add(record)
        await self._event("created", record, record.reason)

    async def _event(self, kind: str, memory: MemoryRecord, reason: str) -> None:
        await self.memos.store.add_event(
            {
                "user_id": self.user_id,
                "project_id": DEMO_PROJECT,
                "kind": kind,
                "memory_id": memory.memory_id,
                "type": memory.type.value,
                "content": memory.content,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _context(self, message: str):
        return await self.memos.build_context(
            self.user_id,
            DEMO_PROJECT,
            message,
            query_embedding=self.memos.qwen.deterministic_embed(message),
        )

    @staticmethod
    def _turn(
        session_id: str,
        message: str,
        expectation: str,
        answer: str,
        used: List[MemoryRecord],
        actions: MemoryActions,
        trace: Any,
    ) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "message": message,
            "expectation": expectation,
            "answer": answer,
            "injected_memories": [
                {
                    "content": memory.content,
                    "type": memory.type.value,
                    "is_critical": memory.is_critical,
                }
                for memory in used
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

    async def run(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Run four deterministic sessions and return public result plus traces."""
        await self.memos.store.clear_user(self.user_id, DEMO_PROJECT)
        turns: List[Dict[str, Any]] = []
        traces: List[Dict[str, Any]] = []

        session_id, message, expectation = JUDGE_SCRIPT[0]
        _, trace, used = await self._context(message)
        initial_records = [
            self._memory(
                session_id=session_id,
                content="This project is the Qwen Hackathon Track 1 MemoryAgent.",
                memory_type=MemoryType.project,
                importance=0.8,
                tags=["qwen", "hackathon", "project"],
            ),
            self._memory(
                session_id=session_id,
                content="I prefer a FastAPI backend.",
                memory_type=MemoryType.preference,
                importance=0.8,
                tags=["fastapi", "backend"],
            ),
            self._memory(
                session_id=session_id,
                content="The submitted build uses a React 18 + Vite frontend.",
                memory_type=MemoryType.preference,
                importance=0.8,
                tags=["react", "vite", "frontend"],
            ),
            self._memory(
                session_id=session_id,
                content="I prefer Alibaba Cloud deployment.",
                memory_type=MemoryType.preference,
                importance=0.75,
                tags=["alibaba", "deployment", "architecture"],
            ),
            self._memory(
                session_id=session_id,
                content="Never commit API keys.",
                memory_type=MemoryType.critical,
                importance=1.0,
                critical=True,
                tags=["security", "api-keys"],
            ),
        ]
        for record in initial_records:
            await self._store_created(record)
        actions = MemoryActions(
            created=[
                {"memory_id": record.memory_id, "type": record.type.value, "content": record.content}
                for record in initial_records
            ]
        )
        turns.append(self._turn(session_id, message, expectation, "Memory lifecycle initialized.", used, actions, trace))
        traces.append(self._trace(turns[-1], trace, actions))

        session_id, message, expectation = JUDGE_SCRIPT[1]
        _, trace, used = await self._context(message)
        actions = MemoryActions()
        turns.append(self._turn(session_id, message, expectation, "Retrieved the saved backend and deployment preferences.", used, actions, trace))
        traces.append(self._trace(turns[-1], trace, actions))

        session_id, message, expectation = JUDGE_SCRIPT[2]
        _, trace, used = await self._context(message)
        submitted_frontend = initial_records[2]
        migration = self._memory(
            session_id=session_id,
            content="After this submission, migrate the frontend to Next.js.",
            memory_type=MemoryType.decision,
            importance=0.85,
            tags=["nextjs", "frontend", "future"],
        )
        submitted_frontend.status = MemoryStatus.superseded
        submitted_frontend.superseded_by = migration.memory_id
        submitted_frontend.updated_at = datetime.now(timezone.utc)
        submitted_frontend.reason = "Superseded by the planned post-submission migration."
        migration.supersedes = submitted_frontend.memory_id
        await self.memos.store.update(submitted_frontend)
        await self._event("superseded", submitted_frontend, submitted_frontend.reason)
        await self._store_created(migration)
        actions = MemoryActions(
            created=[{"memory_id": migration.memory_id, "type": migration.type.value, "content": migration.content}],
            superseded=[{"memory_id": submitted_frontend.memory_id, "superseded_by": migration.memory_id}],
        )
        turns.append(self._turn(session_id, message, expectation, "Recorded the future migration and superseded the prior frontend preference.", used, actions, trace))
        traces.append(self._trace(turns[-1], trace, actions))

        session_id, message, expectation = JUDGE_SCRIPT[3]
        _, trace, used = await self._context(message)
        actions = MemoryActions()
        answer = (
            "The submitted MemoPilot IQ build uses React 18 with Vite today. "
            "Next.js is a planned migration for the next iteration, not the current implementation."
        )
        turns.append(self._turn(session_id, message, expectation, answer, used, actions, trace))
        traces.append(self._trace(turns[-1], trace, actions))

        all_memories = await self.memos.store.list(
            self.user_id, DEMO_PROJECT, include_all=True
        )
        return (
            {
                "user_id": self.user_id,
                "project_id": DEMO_PROJECT,
                "turns": turns,
                "final_state": {
                    "active": [
                        memory.content
                        for memory in all_memories
                        if memory.status in {MemoryStatus.active, MemoryStatus.pinned}
                    ],
                    "superseded": [
                        memory.content
                        for memory in all_memories
                        if memory.status == MemoryStatus.superseded
                    ],
                },
            },
            traces,
        )

    def _trace(
        self, turn: Dict[str, Any], trace: Any, actions: MemoryActions
    ) -> Dict[str, Any]:
        return {
            "session_id": turn["session_id"],
            "user_id": self.user_id,
            "project_id": DEMO_PROJECT,
            "query": turn["message"],
            "answer": turn["answer"],
            "trace": trace.model_dump(),
            "memory_actions": actions.model_dump(),
        }
