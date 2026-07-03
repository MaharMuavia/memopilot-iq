"""LoCoMo benchmark adapter for MemoryOS.

LoCoMo (Maharana et al., ACL 2024) is the standard long-conversation memory
benchmark used by Mem0, Zep, and A-Mem: very long multi-session dialogues
(~19 sessions, hundreds of turns) annotated with QA pairs across five
categories. This module adapts it to MemoryOS so MemoPilot IQ can be evaluated
head-to-head with published systems on a shared protocol.

Pipeline per conversation:
  1. **Ingest** every dialogue turn into the memory store, either
     ``verbatim`` (one memory per turn, tagged with its ``dia_id``) or
     ``extract`` (through the full Memory Editor extraction pass).
  2. **Answer** each QA pair with the standard retrieve -> score -> budget
     context assembly, asking the LLM for a short answer.
  3. **Grade** with the benchmark's standard automatic metrics: normalized
     token-level F1 and exact match (SQuAD-style normalization), reported
     overall and per category. We additionally report **evidence recall**: the
     fraction of questions for which at least one annotated evidence turn was
     injected into the context — a model-independent measure of the memory
     layer itself (available in ``verbatim`` mode, and offline).

Category names follow the official evaluation: 1 multi-hop, 2 temporal,
3 open-domain, 4 single-hop, 5 adversarial. Category 5 (whose gold field is
``adversarial_answer``) is skipped by default, matching Mem0's public protocol.

The dataset itself is NOT redistributed here; fetch it from the official repo
(``scripts/run_locomo.py --download``) into ``backend/data/`` (git-ignored).
"""
from __future__ import annotations

import json
import re
import string
import time
from collections import Counter, defaultdict
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ..memory import MemoryOS
from ..models import MemoryRecord, MemoryType
from ..utils.logging import get_logger

logger = get_logger("locomo")

LOCOMO_URL = "https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json"

CATEGORY_NAMES = {
    1: "multi_hop",
    2: "temporal",
    3: "open_domain",
    4: "single_hop",
    5: "adversarial",
}

_ANSWER_INSTRUCTION = (
    "Based on your memory of the conversation, answer the question with a "
    "short phrase only (a few words, no explanation)."
)


# --------------------------------------------------------------------------
# Standard SQuAD-style grading (the automatic metric used with LoCoMo)
# --------------------------------------------------------------------------
_ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalize_answer(text: str) -> str:
    text = str(text).lower()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    text = _ARTICLES.sub(" ", text)
    return " ".join(text.split())


def token_f1(prediction: str, gold: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = Counter(pred_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, gold: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(gold))


# --------------------------------------------------------------------------
# Dataset access
# --------------------------------------------------------------------------
def load_locomo(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Unexpected LoCoMo format: expected a list of samples.")
    return data


def iter_sessions(conversation: Dict[str, Any]) -> Iterator[Tuple[str, str, List[dict]]]:
    """Yield ``(session_key, date_time, turns)`` in session order."""
    keys = sorted(
        (k for k in conversation
         if re.fullmatch(r"session_\d+", k) and isinstance(conversation[k], list)),
        key=lambda k: int(k.split("_")[1]),
    )
    for key in keys:
        yield key, str(conversation.get(f"{key}_date_time", "")), conversation[key]


def turn_text(turn: Dict[str, Any]) -> str:
    text = str(turn.get("text", "")).strip()
    caption = turn.get("blip_caption")
    if caption:
        text = f"{text} [shares a photo: {caption}]".strip()
    return text


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
class LoCoMoRunner:
    def __init__(self, memos: MemoryOS) -> None:
        self.memos = memos

    async def run(
        self,
        path: str,
        mode: str = "verbatim",
        max_conversations: Optional[int] = None,
        max_qa_per_conversation: Optional[int] = None,
        include_adversarial: bool = False,
        retrieval_only: bool = False,
        checkpoint_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the benchmark. When ``checkpoint_path`` is given, per-QA results
        and per-sample ingestion are persisted incrementally so an interrupted
        run resumes without repeating API calls (the memory store must be kept
        between runs, i.e. a stable DATABASE_URL)."""
        samples = load_locomo(path)
        if max_conversations:
            samples = samples[:max_conversations]

        ck = self._load_checkpoint(checkpoint_path)
        agg = defaultdict(lambda: {"f1": 0.0, "em": 0.0, "ev": 0.0, "ev_n": 0, "n": 0})
        total_turns = 0
        t_start = time.perf_counter()

        for sample in samples:
            sample_id = str(sample.get("sample_id", "unknown"))
            user = f"locomo-{sample_id}"
            project = "locomo"

            # Ingestion (reused across resumes when the checkpoint marker
            # matches the persisted store).
            ingested_marker = ck["ingested"].get(sample_id, 0)
            existing = 0
            if checkpoint_path and ingested_marker:
                existing = len(await self.memos.store.list(user, project, include_all=True))
            if checkpoint_path and ingested_marker and existing >= ingested_marker:
                total_turns += ingested_marker
                logger.info("LoCoMo sample %s: reusing %d ingested turns.",
                            sample_id, ingested_marker)
            else:
                await self.memos.store.clear_user(user, project)
                n = await self._ingest(sample["conversation"], user, project, mode)
                total_turns += n
                if checkpoint_path:
                    ck["ingested"][sample_id] = n
                    self._save_checkpoint(checkpoint_path, ck)

            qa_items = [
                q for q in sample.get("qa", [])
                if include_adversarial or q.get("category") != 5
            ]
            if max_qa_per_conversation:
                qa_items = qa_items[:max_qa_per_conversation]

            for idx, qa in enumerate(qa_items):
                key = f"{sample_id}::{idx}"
                cached = (
                    ck["answers"].get(key)
                    if checkpoint_path and not retrieval_only else None
                )
                if cached is not None:
                    bucket = agg[cached["category"]]
                    bucket["f1"] += cached["f1"]
                    bucket["em"] += cached["em"]
                    if "ev" in cached:
                        bucket["ev"] += cached["ev"]
                        bucket["ev_n"] += 1
                    bucket["n"] += 1
                    continue

                cat = CATEGORY_NAMES.get(qa.get("category"), f"category_{qa.get('category')}")
                gold = qa.get("answer", qa.get("adversarial_answer", ""))
                question = str(qa.get("question", ""))

                system_prompt, trace, used = await self.memos.build_context(
                    user, project, question
                )

                # Evidence recall (model-independent; verbatim mode tags dia_ids).
                evidence = set(qa.get("evidence") or [])
                bucket = agg[cat]
                entry: Dict[str, Any] = {"category": cat, "f1": 0.0, "em": 0.0}
                if evidence and mode == "verbatim":
                    injected_dia = {t for m in used for t in m.tags}
                    ev_hit = float(bool(evidence & injected_dia))
                    bucket["ev"] += ev_hit
                    bucket["ev_n"] += 1
                    entry["ev"] = ev_hit

                if not retrieval_only:
                    answer = await self.memos.qwen.chat([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{_ANSWER_INSTRUCTION}\n\nQuestion: {question}"},
                    ])
                    entry["f1"] = token_f1(answer, str(gold))
                    entry["em"] = exact_match(answer, str(gold))
                    entry["question"] = question
                    entry["gold"] = str(gold)
                    entry["prediction"] = answer
                    bucket["f1"] += entry["f1"]
                    bucket["em"] += entry["em"]
                bucket["n"] += 1

                if checkpoint_path and not retrieval_only:
                    ck["answers"][key] = entry
                    self._save_checkpoint(checkpoint_path, ck)

            # Keep the store when checkpointing so a resumed run can reuse it.
            if not checkpoint_path:
                await self.memos.store.clear_user(user, project)
            logger.info("LoCoMo sample %s done (%d QA graded).", sample_id, len(qa_items))

        by_category = {}
        tot = {"f1": 0.0, "em": 0.0, "ev": 0.0, "ev_n": 0, "n": 0}
        for cat, b in sorted(agg.items()):
            by_category[cat] = self._finalize(b)
            for k in tot:
                tot[k] += b[k]
        return {
            "dataset": "LoCoMo (locomo10)",
            "mode": mode,
            "retrieval_only": retrieval_only,
            "conversations": len(samples),
            "turns_ingested": total_turns,
            "elapsed_s": round(time.perf_counter() - t_start, 1),
            "overall": self._finalize(tot),
            "by_category": by_category,
        }

    async def _ingest(
        self, conversation: Dict[str, Any], user: str, project: str, mode: str
    ) -> int:
        count = 0
        for session_key, date, turns in iter_sessions(conversation):
            for turn in turns:
                text = turn_text(turn)
                if not text:
                    continue
                speaker = str(turn.get("speaker", "speaker"))
                content = f"{speaker} said ({date}): {text}"
                if mode == "extract":
                    await self.memos.remember(
                        user_id=user, project_id=project,
                        session_id=session_key, message=content,
                    )
                else:  # verbatim: one memory per turn, tagged with its dia_id
                    record = MemoryRecord(
                        user_id=user, project_id=project, session_id=session_key,
                        type=MemoryType.project, content=content,
                        summary=text[:80],
                        tags=[str(turn.get("dia_id", ""))],
                        importance=0.5, confidence=0.9,
                        reason="LoCoMo verbatim turn.",
                    )
                    record.embedding = await self.memos.qwen.embed(content)
                    await self.memos.store.add(record)
                count += 1
        return count

    @staticmethod
    def _load_checkpoint(path: Optional[str]) -> Dict[str, Any]:
        if path:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    ck = json.load(fh)
                if isinstance(ck, dict) and "answers" in ck and "ingested" in ck:
                    logger.info("Resuming from checkpoint %s (%d answers cached).",
                                path, len(ck["answers"]))
                    return ck
            except FileNotFoundError:
                pass
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Ignoring unreadable checkpoint %s: %s", path, exc)
        return {"ingested": {}, "answers": {}}

    @staticmethod
    def _save_checkpoint(path: str, ck: Dict[str, Any]) -> None:
        import os

        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(ck, fh)
        # On Windows os.replace raises PermissionError if a reader (editor,
        # progress watcher) briefly holds the destination open. Retry with
        # backoff; a skipped save is harmless because we save on every QA.
        for attempt in range(6):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                time.sleep(0.2 * (attempt + 1))
        logger.warning("Checkpoint save skipped (destination locked): %s", path)

    @staticmethod
    def _finalize(b: Dict[str, float]) -> Dict[str, Any]:
        n = max(1, b["n"])
        out: Dict[str, Any] = {
            "n": b["n"],
            "f1": round(b["f1"] / n, 3),
            "exact_match": round(b["em"] / n, 3),
        }
        if b["ev_n"]:
            out["evidence_recall"] = round(b["ev"] / b["ev_n"], 3)
        return out
