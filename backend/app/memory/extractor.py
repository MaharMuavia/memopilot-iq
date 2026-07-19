"""Memory extraction pipeline.

After each user message, the extractor:
  1. Redacts secrets, then asks Qwen (the "Memory Editor") to extract stable,
     useful long-term memories as strict JSON.
  2. Drops anything secret-like.
  3. Detects contradictions with existing active memories and supersedes them.
  4. Sets ``expires_at`` for temporary/deadline memories.
  5. Merges near-duplicate memories instead of creating duplicates.
  6. Generates embeddings and persists the structured records.
  7. Emits memory-timeline events.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from ..models import (
    MemoryActions,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    PrivacyLevel,
)
from ..qwen_client import QwenClient
from ..utils.logging import get_logger
from .classifier import TOPIC_GROUPS, topic_of  # noqa: F401 (re-exported)
from .safety import safety_engine
from .supersession import find_contradictions

logger = get_logger("extractor")


def contains_secret(text: str) -> bool:
    return safety_engine.has_secret(text)


def redact_secrets(text: str) -> str:
    return safety_engine.redact(text)

EXTRACTOR_SYSTEM_PROMPT = """You are the Memory Editor for MemoPilot IQ.
Extract useful long-term memories only from the user's message.
Do not extract facts from assistant messages unless they reflect a confirmed user decision.
Never store API keys, passwords, tokens, private credentials, or sensitive secrets.
Detect preferences, decisions, constraints, goals, mistakes, deadlines, and critical instructions.
Detect contradictions with existing memories.
Return strict JSON only.

JSON format:
{
  "new_memories": [
    {
      "type": "preference | project | decision | mistake | constraint | deadline | learning_goal | task | critical | temporary",
      "content": "...",
      "summary": "...",
      "importance": 0.0,
      "confidence": 0.0,
      "tags": ["..."],
      "expires_at": null,
      "is_critical": false,
      "privacy_level": "public | private | sensitive",
      "reason": "why this should be remembered"
    }
  ],
  "updates": [
    {"old_memory_id": "...", "action": "merge | supersede | archive | update_importance", "new_content": "...", "reason": "..."}
  ],
  "forget": [
    {"memory_id": "...", "action": "expire | archive | delete", "reason": "..."}
  ]
}"""

_CONTRADICTION_CUES = [
    "instead", "changed my mind", "actually", "no longer", "replace", "switch to",
    "rather than", "not anymore", "use .* instead",
]

_EXPLICIT_MEMORY_INTENT = re.compile(
    r"\bremember\s+(?:this|that|it|for\s+later)\b|"
    r"\b(?:save|store|keep|note)\s+(?:this|that|it)\s+(?:for\s+later|as\s+a\s+memory)\b",
    re.IGNORECASE,
)

_NON_DURABLE_REQUEST_START = re.compile(
    r"^(?:what|which|who|why|when|where|how|can|could|would|should|do|does|"
    r"is|are|design|show|explain|tell|give|write|create|generate|summarize|"
    r"analyse|analyze|help)\b",
    re.IGNORECASE,
)

_DURABLE_SIGNAL = re.compile(
    r"\b(?:i|we)\s+(?:prefer|want|need|decided|use|will|am|are)\b|"
    r"\b(?:my|our)\s+[^.!?]{1,80}\s+is\b|"
    r"^(?:use|prefer|remember|never|must|do not|don't|temporary note|deadline)\b|"
    r"\b(?:changed my mind|switch to|migrate|after this submission|forget|archive)\b",
    re.IGNORECASE,
)


def should_extract_memory(message: str) -> bool:
    """Return False for pure requests that cannot contain durable user facts."""
    stripped = message.strip()
    if not stripped:
        return False
    if _EXPLICIT_MEMORY_INTENT.search(stripped):
        return True
    # Check request-leading verbs before broad first-person signals. Without
    # this ordering, "What backend should I use?" is misread as the durable
    # statement "I use ..." and triggers an unnecessary provider call.
    if _NON_DURABLE_REQUEST_START.match(stripped):
        return False
    if _DURABLE_SIGNAL.search(stripped):
        return True
    if "?" in stripped:
        return False
    return True

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class MemoryExtractor:
    def __init__(self, qwen: QwenClient, store) -> None:
        self.qwen = qwen
        self.store = store

    def _build_user_prompt(
        self, message: str, existing: List[MemoryRecord]
    ) -> str:
        existing_block = "\n".join(
            f"- ({m.memory_id}) [{m.type.value}] {m.content}" for m in existing[:30]
        ) or "(none)"
        return (
            f"EXISTING ACTIVE MEMORIES:\n{existing_block}\n\n"
            f"USER MESSAGE:\n{message}"
        )

    async def extract_and_store(
        self,
        *,
        user_id: str,
        project_id: Optional[str],
        session_id: str,
        message: str,
        source_message_id: str,
    ) -> MemoryActions:
        actions = MemoryActions()

        # 1. Redact secrets before anything else touches the text.
        if contains_secret(message):
            actions.redacted.append("Secret-like content detected and redacted before extraction.")
        safe_message = redact_secrets(message)

        # Pure questions and assistant-directed commands contain no durable
        # user fact. Skipping the Memory Editor avoids a second, unnecessary
        # Qwen completion and materially lowers live latency and timeout risk.
        if not should_extract_memory(safe_message):
            return actions

        existing = await self.store.list(
            user_id, project_id, statuses=[MemoryStatus.active.value, MemoryStatus.pinned.value]
        )

        result = await self.qwen.extract_json(
            EXTRACTOR_SYSTEM_PROMPT, self._build_user_prompt(safe_message, existing)
        )

        new_memories: List[Dict[str, Any]] = result.get("new_memories", []) or []
        # The model occasionally treats an explicit "remember this" sentence
        # as conversational filler and returns an empty list. That makes the
        # core product promise unreliable, so use the deterministic extractor
        # only for explicit memory intent. Secret filtering below still guards
        # every resulting record before it is persisted.
        if not new_memories and _EXPLICIT_MEMORY_INTENT.search(safe_message):
            result = self.qwen.deterministic_extract(safe_message)
            new_memories = result.get("new_memories", []) or []
        explicit_contradiction = any(
            re.search(cue, safe_message.lower()) for cue in _CONTRADICTION_CUES
        )
        pending_records: List[MemoryRecord] = []

        for raw in new_memories:
            content = redact_secrets(str(raw.get("content", "")).strip())[:4000]
            if not content or contains_secret(content):
                actions.redacted.append("Dropped a memory that still contained a secret.")
                continue

            record = self._to_record(
                raw, user_id, project_id, session_id, source_message_id, content
            )

            # 4/5. Duplicate detection -> merge instead of duplicate.
            duplicate = self._find_duplicate(existing, record)
            if duplicate:
                duplicate.usage_count += 1
                duplicate.confidence = min(1.0, duplicate.confidence + 0.05)
                duplicate.updated_at = datetime.now(timezone.utc)
                await self.store.update(duplicate)
                actions.updated.append({"memory_id": duplicate.memory_id, "action": "merge_duplicate"})
                await self._event(actions, user_id, project_id, "updated", duplicate, "Merged duplicate memory.")
                continue

            # 3. Contradiction / supersession against same-topic memories.
            superseded = self._find_contradiction(existing, record, explicit_contradiction)
            for old in superseded:
                old.status = MemoryStatus.superseded
                old.superseded_by = record.memory_id
                old.updated_at = datetime.now(timezone.utc)
                old.reason = f"Superseded by newer decision: {record.content[:60]}"
                record.supersedes = old.memory_id
                await self.store.update(old)
                actions.superseded.append({"memory_id": old.memory_id, "superseded_by": record.memory_id})
                await self._event(actions, user_id, project_id, "superseded", old, old.reason)

            # Keep provider embedding calls batched. This avoids a separate
            # network round trip for every extracted fact in one user turn.
            pending_records.append(record)
            actions.created.append({"memory_id": record.memory_id, "type": record.type.value, "content": record.content})

        # 6. Embed and persist accepted new records together. ``embed_many``
        # supplies a same-size deterministic fallback when the provider fails.
        embeddings = await self.qwen.embed_many(
            [record.content for record in pending_records]
        )
        for record, embedding in zip(pending_records, embeddings):
            record.embedding = embedding
            await self.store.add(record)
            existing.append(record)
            await self._event(
                actions, user_id, project_id, "created", record, record.reason
            )

        # Honor the model's structured supersede/archive updates (complements
        # the heuristic contradiction detection above; the LLM is good at
        # spotting "switch from X to Y" phrasings the heuristic may miss).
        for upd in result.get("updates", []) or []:
            old_id = str(upd.get("old_memory_id") or "")
            action = upd.get("action")
            mem = await self.store.get(old_id) if old_id else None
            if (
                not mem
                or mem.user_id != user_id
                or mem.project_id not in {project_id, None}
                or mem.status not in {MemoryStatus.active, MemoryStatus.pinned}
            ):
                continue
            if mem.is_critical:
                continue
            if action == "supersede":
                new_content = redact_secrets(
                    str(upd.get("new_content") or "").strip()
                )[:4000]
                same_turn = [
                    candidate
                    for candidate in existing
                    if candidate.memory_id != mem.memory_id
                    and candidate.source_message_id == source_message_id
                    and candidate.status in {MemoryStatus.active, MemoryStatus.pinned}
                ]
                replacement = None
                if same_turn:
                    replacement = max(
                        same_turn,
                        key=lambda candidate: (
                            _similar(candidate.content, new_content)
                            if new_content
                            else candidate.importance
                        ),
                    )
                elif new_content and not contains_secret(new_content):
                    replacement = self._to_record(
                        {
                            "type": mem.type.value,
                            "content": new_content,
                            "summary": new_content[:80],
                            "importance": max(0.7, mem.importance),
                            "confidence": upd.get("confidence", 0.85),
                            "tags": [*mem.tags, "qwen-update"],
                            "privacy_level": mem.privacy_level.value,
                            "reason": upd.get("reason") or "Replacement from Qwen update.",
                        },
                        user_id,
                        project_id,
                        session_id,
                        source_message_id,
                        new_content,
                    )
                    replacement.embedding = await self.qwen.embed(replacement.content)
                    await self.store.add(replacement)
                    existing.append(replacement)
                    actions.created.append({
                        "memory_id": replacement.memory_id,
                        "type": replacement.type.value,
                        "content": replacement.content,
                    })
                    await self._event(
                        actions,
                        user_id,
                        project_id,
                        "created",
                        replacement,
                        replacement.reason,
                    )

                # A supersede action without a durable replacement would erase
                # the current truth. Preserve the old memory instead.
                if replacement is None:
                    logger.warning(
                        "Ignored Qwen supersede for %s because no replacement was supplied",
                        mem.memory_id,
                    )
                    continue
                replacement.supersedes = mem.memory_id
                await self.store.update(replacement)
                mem.status = MemoryStatus.superseded
                mem.superseded_by = replacement.memory_id
                mem.updated_at = datetime.now(timezone.utc)
                mem.reason = str(upd.get("reason") or "Superseded by a newer decision.")
                await self.store.update(mem)
                actions.superseded.append({
                    "memory_id": mem.memory_id,
                    "superseded_by": replacement.memory_id,
                    "via": "llm_update",
                })
                await self._event(actions, user_id, project_id, "superseded", mem, mem.reason)
            elif action == "archive":
                mem.status = MemoryStatus.archived
                mem.updated_at = datetime.now(timezone.utc)
                await self.store.update(mem)
                actions.forgotten.append({"memory_id": mem.memory_id, "action": "archive"})
                await self._event(actions, user_id, project_id, "archived", mem, str(upd.get("reason") or ""))

        # Explicit forget instructions from the model.
        for f in result.get("forget", []) or []:
            mem = await self.store.get(f.get("memory_id", ""))
            if mem and mem.user_id == user_id and mem.project_id in {project_id, None}:
                mem.status = MemoryStatus.expired if f.get("action") == "expire" else MemoryStatus.archived
                mem.updated_at = datetime.now(timezone.utc)
                await self.store.update(mem)
                actions.forgotten.append({"memory_id": mem.memory_id, "action": f.get("action")})
                await self._event(actions, user_id, project_id, "forgotten", mem, f.get("reason", ""))

        return actions

    def _to_record(
        self,
        raw: Dict[str, Any],
        user_id: str,
        project_id: Optional[str],
        session_id: str,
        source_message_id: str,
        content: str,
    ) -> MemoryRecord:
        try:
            mtype = MemoryType(raw.get("type", "preference"))
        except ValueError:
            mtype = MemoryType.preference

        expires_at = self._parse_expiry(raw, mtype, content)
        privacy = raw.get("privacy_level", "public")
        try:
            privacy_level = PrivacyLevel(privacy)
        except ValueError:
            privacy_level = PrivacyLevel.public

        # Provider JSON is untrusted. Criticality must agree with the validated
        # memory type; otherwise an ordinary preference can bypass relevance
        # admission and consume context on every future turn.
        is_critical = mtype == MemoryType.critical
        # Model output is untrusted. Clamp it before Pydantic validates the
        # record so one malformed extraction cannot break the chat request or
        # inflate a context window.
        def bounded_float(value: Any, default: float) -> float:
            try:
                return min(1.0, max(0.0, float(value)))
            except (TypeError, ValueError):
                return default

        return MemoryRecord(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            type=mtype,
            status=MemoryStatus.active,
            content=content,
            summary=redact_secrets(str(raw.get("summary") or content[:80]))[:500],
            importance=bounded_float(raw.get("importance"), 0.6),
            confidence=bounded_float(raw.get("confidence"), 0.75),
            tags=[redact_secrets(str(t))[:64] for t in (raw.get("tags") or [])][:8],
            source_message_id=source_message_id,
            is_critical=is_critical,
            privacy_level=privacy_level,
            expires_at=expires_at,
            reason=redact_secrets(
                str(raw.get("reason") or "Extracted by Memory Editor.")
            )[:500],
        )

    def _parse_expiry(
        self, raw: Dict[str, Any], mtype: MemoryType, content: str
    ) -> Optional[datetime]:
        explicit = raw.get("expires_at")
        if explicit:
            try:
                return datetime.fromisoformat(str(explicit).replace("Z", "+00:00"))
            except ValueError:
                pass
        # Temporary memories get a short default lifetime.
        if mtype == MemoryType.temporary:
            return datetime.now(timezone.utc) + timedelta(days=1)
        # Try to read an explicit date out of deadline content.
        if mtype == MemoryType.deadline:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", content)
            if m:
                try:
                    return datetime(int(m[1]), int(m[2]), int(m[3]), tzinfo=timezone.utc)
                except ValueError:
                    return None
        return None

    def _find_duplicate(
        self, existing: List[MemoryRecord], record: MemoryRecord
    ) -> Optional[MemoryRecord]:
        for mem in existing:
            if mem.status not in {MemoryStatus.active, MemoryStatus.pinned}:
                continue
            if mem.type == record.type and _similar(mem.content, record.content) > 0.86:
                return mem
        return None

    def _find_contradiction(
        self,
        existing: List[MemoryRecord],
        record: MemoryRecord,
        explicit_contradiction: bool,
    ) -> List[MemoryRecord]:
        # Delegated to the dedicated supersession engine.
        return find_contradictions(existing, record)

    async def _event(
        self,
        actions: MemoryActions,
        user_id: str,
        project_id: Optional[str],
        kind: str,
        memory: MemoryRecord,
        reason: str,
    ) -> None:
        await self.store.add_event(
            {
                "user_id": user_id,
                "project_id": project_id,
                "kind": kind,
                "memory_id": memory.memory_id,
                "type": memory.type.value,
                "content": memory.content,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
