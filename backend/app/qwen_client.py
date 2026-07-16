"""Qwen Cloud API client (Alibaba Cloud DashScope, OpenAI-compatible mode).

This module is the single integration point with Qwen Cloud. It is used for:
  * chat / reasoning  -> :meth:`QwenClient.chat`
  * memory extraction -> :meth:`QwenClient.extract_json` (JSON-only output)
  * embeddings        -> :meth:`QwenClient.embed`

Robustness requirement: the whole project must run on a laptop with NO API
key. When ``QWEN_API_KEY`` is unset, the client transparently switches to a
deterministic *offline heuristic* implementation so the demo, tests, and
evaluation benchmark still work end-to-end. The UI/health endpoint reports
whether Qwen is actually configured.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, List, Optional

import httpx

from .config import Settings, get_settings
from .utils.logging import get_logger

logger = get_logger("qwen_client")

EMBED_DIM = 256


class QwenClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None
        self._provider_status = "online" if self.settings.qwen_configured else "offline"

    @property
    def online(self) -> bool:
        return self.settings.qwen_configured

    @property
    def provider_status(self) -> str:
        """Current provider state without pretending a failed live call succeeded."""
        return self._provider_status

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.qwen_base_url,
                headers={
                    "Authorization": f"Bearer {self.settings.qwen_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(45.0),
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Chat / reasoning
    # ------------------------------------------------------------------
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        if not self.online:
            return self._offline_chat(messages)
        try:
            client = await self._http()
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": self.settings.qwen_chat_model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._provider_status = "online"
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Qwen chat failed (%s); using offline fallback", exc)
            self._provider_status = "degraded_offline_fallback"
            return self._offline_chat(messages)

    async def extract_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Qwen and parse a strict-JSON response."""
        if not self.online:
            return self._offline_extract(user_prompt)
        try:
            client = await self._http()
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": self.settings.qwen_chat_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            self._provider_status = "online"
            return _safe_json(content)
        except Exception as exc:  # pragma: no cover
            logger.warning("Qwen extract failed (%s); using offline fallback", exc)
            self._provider_status = "degraded_offline_fallback"
            return self._offline_extract(user_prompt)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    async def embed(self, text: str) -> List[float]:
        if not self.online:
            return self._offline_embed(text)
        try:
            client = await self._http()
            resp = await client.post(
                "/embeddings",
                json={"model": self.settings.qwen_embedding_model, "input": text},
            )
            resp.raise_for_status()
            self._provider_status = "online"
            return resp.json()["data"][0]["embedding"]
        except Exception as exc:  # pragma: no cover
            logger.warning("Qwen embed failed (%s); using offline fallback", exc)
            self._provider_status = "degraded_offline_fallback"
            return self._offline_embed(text)

    # ==================================================================
    # Offline deterministic fallbacks (no network, no API key)
    # ==================================================================
    def _offline_chat(self, messages: List[Dict[str, str]]) -> str:
        """A grounded, deterministic assistant for demo/local use.

        It synthesises an answer using the system prompt (which already
        contains the selected memories from the ContextBuilder) and the last
        user message, so memory recall/supersession is observable even with no
        Qwen key configured.
        """
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        mem_lines = re.findall(r"- \[(.*?)\] (.*)", system)
        recalled = "; ".join(line[1] for line in mem_lines[:6])
        prefix = "Using my persistent memory of your project"
        if recalled:
            return (
                f"{prefix}: {recalled}.\n\n"
                f"Regarding \"{user.strip()[:160]}\" — I have applied the "
                f"active preferences and decisions above. (Offline demo mode: "
                f"connect a Qwen API key for full natural-language reasoning.)"
            )
        return (
            f"Regarding \"{user.strip()[:160]}\" — no relevant long-term memory "
            f"was found yet, so I am answering from the current message only. "
            f"(Offline demo mode.)"
        )

    def _offline_extract(self, user_prompt: str) -> Dict[str, Any]:
        """Heuristic memory extraction so the pipeline works without Qwen.

        We parse the *user message* (the extractor prompt embeds it after the
        marker 'USER MESSAGE:'). Splits on connectives and classifies each
        clause into a memory type using keyword cues.
        """
        msg = user_prompt
        m = re.search(r"USER MESSAGE:\s*(.*)", user_prompt, re.DOTALL)
        if m:
            msg = m.group(1)
        msg = msg.strip().strip('"')

        # Split on sentence/clause boundaries. Use ``\.\s+`` (period + space) so
        # tokens like "Next.js" stay intact.
        clauses = re.split(r"\.\s+|\n|,| and | but ", msg)
        new_memories: List[Dict[str, Any]] = []
        # Filler/command clauses that are requests to the assistant, not durable
        # facts about the user — skipped so the store stays clean.
        _filler = {"actually", "i changed my mind", "please", "thanks"}
        _question_starts = (
            "what", "how", "why", "when", "where", "who", "which", "should",
            "could", "would", "can", "do ", "does", "is ", "are ", "remind",
            "design", "show", "explain", "tell", "give", "write", "create",
        )
        for raw in clauses:
            clause = raw.strip()
            if len(clause) < 6:
                continue
            low = clause.lower()
            # Skip questions and assistant-directed commands.
            if "?" in clause or low in _filler or low.startswith(_question_starts):
                continue
            mtype = "preference"
            importance = 0.55
            is_critical = False
            expires_at = None
            if any(k in low for k in ["never", "do not", "don't", "must not"]):
                mtype = "critical"
                importance = 0.95
                is_critical = True
            elif any(k in low for k in ["temporary", "today only", "for now", "right now", "just today", "temp note"]):
                mtype = "temporary"
                importance = 0.4
            elif any(k in low for k in ["deadline", "due", "by july", "by june", "submission"]):
                mtype = "deadline"
                importance = 0.8
            elif any(k in low for k in ["instead", "changed my mind", "actually", "replace"]):
                mtype = "decision"
                importance = 0.8
            elif any(k in low for k in ["learning", "studying", "study", "learn"]):
                mtype = "learning_goal"
                importance = 0.6
            elif any(k in low for k in ["building", "project is", "this project", "for the"]):
                mtype = "project"
                importance = 0.75
            elif any(k in low for k in ["prefer", "like", "use ", "want", "i'd like"]):
                mtype = "preference"
                importance = 0.65
            new_memories.append(
                {
                    "type": mtype,
                    "content": clause,
                    "summary": clause[:80],
                    "importance": importance,
                    "confidence": 0.75,
                    "tags": _keywords(clause),
                    "expires_at": expires_at,
                    "is_critical": is_critical,
                    "privacy_level": "public",
                    "reason": f"Offline heuristic classified this as a {mtype}.",
                }
            )
        return {"new_memories": new_memories, "updates": [], "forget": []}

    def _offline_embed(self, text: str) -> List[float]:
        """Deterministic hashing embedding (bag-of-words into EMBED_DIM)."""
        vec = [0.0] * EMBED_DIM
        for token in _keywords(text, limit=64):
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = h % EMBED_DIM
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def _keywords(text: str, limit: int = 12) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{2,}", text.lower())
    stop = {
        "the", "and", "for", "with", "this", "that", "you", "are", "use",
        "using", "have", "want", "like", "into", "from", "should", "would",
        "but", "not", "all", "your", "our", "can", "will",
    }
    out: List[str] = []
    for w in words:
        if w in stop:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


def _safe_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    # Strip markdown fences if the model wrapped the JSON.
    content = re.sub(r"^```(json)?", "", content).strip()
    content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {"new_memories": [], "updates": [], "forget": []}
