"""MemoryOS facade.

This package wires the MemoryOS components together and exposes a single
high-level :class:`MemoryOS` object used by the API routes:

    extractor + retriever + scorer + context_builder + forgetting + store

It also owns the store-selection logic (local SQLite vs Alibaba Tablestore)
with a safe fallback to SQLite when cloud credentials are missing.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from ..config import ALIBABA_CLOUD_MODE, Settings, get_settings
from ..models import MemoryActions, MemoryRecord, MemoryTrace
from ..qwen_client import QwenClient
from ..utils.logging import get_logger
from .context_builder import ContextBuilder
from .extractor import MemoryExtractor
from .forgetting import ForgettingEngine
from .reflection import ReflectionEngine
from .retriever import HybridRetriever
from .store_base import MemoryStore
from .store_sqlite import SQLiteMemoryStore

logger = get_logger("memoryos")


def build_store(settings: Settings) -> MemoryStore:
    """Pick the memory store backend based on settings, with safe fallback."""
    if settings.resolved_mode() == ALIBABA_CLOUD_MODE:
        try:
            from .store_alibaba import AlibabaTablestoreMemoryStore

            logger.info("Using Alibaba Cloud Tablestore memory store.")
            return AlibabaTablestoreMemoryStore(settings)
        except Exception as exc:  # pragma: no cover - cloud SDK missing
            logger.warning(
                "Alibaba store unavailable (%s); falling back to SQLite.", exc
            )
    return SQLiteMemoryStore(settings.database_url)


class MemoryOS:
    """High-level orchestrator over all MemoryOS components."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.qwen = QwenClient(self.settings)
        self.store: MemoryStore = build_store(self.settings)
        self.retriever = HybridRetriever(self.store)
        self.extractor = MemoryExtractor(self.qwen, self.store)
        self.forgetting = ForgettingEngine(self.store)
        self.reflection = ReflectionEngine(self.store, self.qwen)
        self.context_builder = ContextBuilder(
            token_budget=self.settings.memory_token_budget,
            top_k=self.settings.retrieval_top_k,
        )

    async def init(self) -> None:
        await self.store.init()

    @property
    def mode(self) -> str:
        return self.settings.resolved_mode()

    async def build_context(
        self, user_id: str, project_id: Optional[str], message: str
    ) -> Tuple[str, MemoryTrace, List[MemoryRecord]]:
        """Retrieve + score + budget into a system prompt and trace."""
        # Expire/archive before retrieval so stale memories never leak in.
        await self.forgetting.sweep(user_id, project_id)
        query_embedding = await self.qwen.embed(message)
        scored, considered, latency = await self.retriever.retrieve(
            user_id, project_id, message, query_embedding,
            top_k=self.settings.retrieval_top_k,
        )
        system_prompt, trace, used = self.context_builder.build(
            message, scored, project_id, considered, latency
        )
        # Mark used memories' usage stats.
        for mem in used:
            mem.usage_count += 1
            from datetime import datetime, timezone

            mem.last_used_at = datetime.now(timezone.utc)
            await self.store.update(mem)
        return system_prompt, trace, used

    async def remember(
        self,
        *,
        user_id: str,
        project_id: Optional[str],
        session_id: str,
        message: str,
    ) -> MemoryActions:
        return await self.extractor.extract_and_store(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            message=message,
            source_message_id=f"msg_{uuid.uuid4().hex[:10]}",
        )
