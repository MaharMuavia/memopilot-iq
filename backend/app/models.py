"""Pydantic models for MemoPilot IQ.

These models define the MemoryRecord schema (the heart of MemoryOS), the
API request/response payloads, and the trace/evaluation structures.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field


ShortTag = Annotated[str, Field(max_length=64)]


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
    user_id: str = Field(min_length=1, max_length=128)
    project_id: Optional[str] = Field(default=None, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    type: MemoryType = MemoryType.preference
    status: MemoryStatus = MemoryStatus.active
    content: str = Field(min_length=1, max_length=4000)
    summary: str = Field(default="", max_length=500)
    embedding: Optional[List[float]] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    recency_score: float = 1.0
    usage_count: int = 0
    source_message_id: str = ""
    tags: List[ShortTag] = Field(default_factory=list, max_length=8)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    is_critical: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.public
    reason: str = Field(default="", max_length=500)

    def public_view(self) -> Dict[str, Any]:
        """Serialisable view without the (large) embedding vector."""
        data = self.model_dump(mode="json")
        data.pop("embedding", None)
        return data


# --------------------------------------------------------------------------
# API payloads
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=128)
    project_id: Optional[str] = Field(default="qwen-memoryagent", max_length=128)
    session_id: str = Field(default="session-001", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)


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
    user_id: str = Field(default="demo-user", min_length=1, max_length=128)
    project_id: Optional[str] = Field(default="qwen-memoryagent", max_length=128)
    session_id: str = Field(default="manual", min_length=1, max_length=128)
    type: MemoryType = MemoryType.preference
    content: str = Field(min_length=1, max_length=4000)
    summary: str = Field(default="", max_length=500)
    importance: float = Field(default=0.6, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    tags: List[ShortTag] = Field(default_factory=list, max_length=8)
    is_critical: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.public
    expires_at: Optional[datetime] = None
    reason: str = Field(default="Manually created", max_length=500)


class UpdateMemoryRequest(BaseModel):
    status: Optional[MemoryStatus] = None
    content: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    summary: Optional[str] = Field(default=None, max_length=500)
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_critical: Optional[bool] = None
    tags: Optional[List[ShortTag]] = Field(default=None, max_length=8)
    pin: Optional[bool] = None
    archive: Optional[bool] = None


class ExtractRequest(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=128)
    project_id: Optional[str] = Field(default="qwen-memoryagent", max_length=128)
    session_id: str = Field(default="session-001", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)
