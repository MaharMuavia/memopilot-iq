"""Pydantic models for MemoPilot IQ.

These models define the MemoryRecord schema (the heart of MemoryOS), the
API request/response payloads, and the trace/evaluation structures.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str = "mem") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MemoryType(str, Enum):
    preference = "preference"
    project = "project"
    decision = "decision"
    mistake = "mistake"
    constraint = "constraint"
    deadline = "deadline"
    learning_goal = "learning_goal"
    task = "task"
    critical = "critical"
    temporary = "temporary"
    outdated = "outdated"
    deleted_by_user = "deleted_by_user"


class MemoryStatus(str, Enum):
    active = "active"
    pinned = "pinned"
    archived = "archived"
    expired = "expired"
    superseded = "superseded"
    deleted = "deleted"


class PrivacyLevel(str, Enum):
    public = "public"
    private = "private"
    sensitive = "sensitive"


class MemoryRecord(BaseModel):
    """A single structured long-term memory."""

    memory_id: str = Field(default_factory=lambda: _new_id("mem"))
    user_id: str
    project_id: Optional[str] = None
    session_id: str
    type: MemoryType = MemoryType.preference
    status: MemoryStatus = MemoryStatus.active
    content: str
    summary: str = ""
    embedding: Optional[List[float]] = None
    importance: float = 0.5
    confidence: float = 0.7
    recency_score: float = 1.0
    usage_count: int = 0
    source_message_id: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    is_critical: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.public
    reason: str = ""

    def public_view(self) -> Dict[str, Any]:
        """Serialisable view without the (large) embedding vector."""
        data = self.model_dump(mode="json")
        data.pop("embedding", None)
        return data


# --------------------------------------------------------------------------
# API payloads
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_id: str = "demo-user"
    project_id: Optional[str] = "qwen-memoryagent"
    session_id: str = "session-001"
    message: str


class ScoredMemory(BaseModel):
    memory: Dict[str, Any]
    score: float
    components: Dict[str, float]
    included: bool
    reason: str
    approx_tokens: int


class MemoryTrace(BaseModel):
    included: List[ScoredMemory] = Field(default_factory=list)
    skipped: List[ScoredMemory] = Field(default_factory=list)
    token_budget: int = 0
    tokens_used: int = 0
    candidates_considered: int = 0
    retrieval_latency_ms: float = 0.0
    notes: List[str] = Field(default_factory=list)


class MemoryActions(BaseModel):
    created: List[Dict[str, Any]] = Field(default_factory=list)
    updated: List[Dict[str, Any]] = Field(default_factory=list)
    superseded: List[Dict[str, Any]] = Field(default_factory=list)
    forgotten: List[Dict[str, Any]] = Field(default_factory=list)
    redacted: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    used_memories: List[Dict[str, Any]]
    memory_actions: MemoryActions
    trace: MemoryTrace
    mode: str


class CreateMemoryRequest(BaseModel):
    user_id: str = "demo-user"
    project_id: Optional[str] = "qwen-memoryagent"
    session_id: str = "manual"
    type: MemoryType = MemoryType.preference
    content: str
    summary: str = ""
    importance: float = 0.6
    confidence: float = 0.8
    tags: List[str] = Field(default_factory=list)
    is_critical: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.public
    expires_at: Optional[datetime] = None
    reason: str = "Manually created"


class UpdateMemoryRequest(BaseModel):
    status: Optional[MemoryStatus] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[float] = None
    is_critical: Optional[bool] = None
    tags: Optional[List[str]] = None
    pin: Optional[bool] = None
    archive: Optional[bool] = None


class ExtractRequest(BaseModel):
    user_id: str = "demo-user"
    project_id: Optional[str] = "qwen-memoryagent"
    session_id: str = "session-001"
    message: str
