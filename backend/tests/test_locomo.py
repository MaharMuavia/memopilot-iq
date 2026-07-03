"""Tests for the LoCoMo benchmark adapter (offline, deterministic)."""
from __future__ import annotations

import json

import pytest

from app.eval.locomo import (
    LoCoMoRunner,
    exact_match,
    iter_sessions,
    load_locomo,
    normalize_answer,
    token_f1,
    turn_text,
)

FIXTURE = [{
    "sample_id": "t1",
    "conversation": {
        "speaker_a": "Ana",
        "speaker_b": "Ben",
        "session_1_date_time": "1:00 pm on 2 Jan, 2024",
        "session_1": [
            {"speaker": "Ana", "dia_id": "D1:1",
             "text": "I just adopted a golden retriever named Biscuit!"},
            {"speaker": "Ben", "dia_id": "D1:2",
             "text": "Congrats! I finally finished my marathon training plan."},
        ],
        "session_2_date_time": "9:00 am on 5 Mar, 2024",
        "session_2": [
            {"speaker": "Ana", "dia_id": "D2:1",
             "text": "Biscuit chewed my headphones so I bought new ones.",
             "blip_caption": "a dog next to broken headphones"},
        ],
    },
    "qa": [
        {"question": "What is the name of Ana's golden retriever?",
         "answer": "Biscuit", "evidence": ["D1:1"], "category": 4},
        {"question": "Did Ana ever meet Ben's cousin?",
         "adversarial_answer": "Not mentioned", "evidence": [], "category": 5},
    ],
}]


# ------------------------------------------------------------- grading
def test_normalization_and_f1():
    assert normalize_answer("The Eiffel Tower!") == "eiffel tower"
    assert token_f1("The Eiffel Tower", "eiffel tower") == 1.0
    assert exact_match("Biscuit.", "biscuit") == 1.0
    assert token_f1("blue car", "red bike") == 0.0
    assert 0.0 < token_f1("a golden retriever puppy", "golden retriever") < 1.0


# ------------------------------------------------------------- parsing
def test_loader_and_session_iteration(tmp_path):
    path = tmp_path / "mini.json"
    path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    samples = load_locomo(str(path))
    assert len(samples) == 1
    sessions = list(iter_sessions(samples[0]["conversation"]))
    assert [s[0] for s in sessions] == ["session_1", "session_2"]
    assert "2 Jan, 2024" in sessions[0][1]
    # image captions are appended to turn text
    assert "shares a photo" in turn_text(samples[0]["conversation"]["session_2"][0])


# ------------------------------------------------------- end-to-end run
@pytest.mark.asyncio
async def test_runner_retrieval_only(memos, tmp_path):
    path = tmp_path / "mini.json"
    path.write_text(json.dumps(FIXTURE), encoding="utf-8")

    report = await LoCoMoRunner(memos).run(str(path), retrieval_only=True)
    assert report["conversations"] == 1
    assert report["turns_ingested"] == 3
    # adversarial (cat 5) skipped by default -> only the single-hop question
    assert report["overall"]["n"] == 1
    single = report["by_category"]["single_hop"]
    # The evidence turn D1:1 must be retrieved into context for this query.
    assert single["evidence_recall"] == 1.0


@pytest.mark.asyncio
async def test_runner_full_answers_offline(memos, tmp_path):
    path = tmp_path / "mini.json"
    path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    report = await LoCoMoRunner(memos).run(str(path), include_adversarial=True)
    assert report["overall"]["n"] == 2
    assert "adversarial" in report["by_category"]
    # F1/EM keys exist and are bounded (offline fallback answers score low).
    assert 0.0 <= report["overall"]["f1"] <= 1.0


@pytest.mark.asyncio
async def test_checkpoint_resume_skips_api_calls(memos, tmp_path):
    path = tmp_path / "mini.json"
    path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    ckpt = str(tmp_path / "ck.json")

    calls = {"chat": 0}
    original_chat = memos.qwen.chat

    async def counting_chat(messages, **kw):
        calls["chat"] += 1
        return await original_chat(messages, **kw)

    memos.qwen.chat = counting_chat

    first = await LoCoMoRunner(memos).run(str(path), checkpoint_path=ckpt)
    chat_after_first = calls["chat"]
    assert chat_after_first >= 1  # one answered QA (cat 5 skipped)

    # Second run resumes: identical aggregates, zero new chat calls,
    # and ingestion is reused from the persisted store.
    second = await LoCoMoRunner(memos).run(str(path), checkpoint_path=ckpt)
    assert calls["chat"] == chat_after_first
    assert second["overall"]["n"] == first["overall"]["n"]
    assert second["overall"]["f1"] == first["overall"]["f1"]
