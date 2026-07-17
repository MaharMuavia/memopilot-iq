"""Generate the deterministic evidence reported in the paper.

The script disables all model-provider credentials before importing the
application. Its answer text comes from the offline fallback and is retained in
the raw diagnostic for debugging only. The paper reports retrieval and
governance metrics, not offline answer accuracy.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

# python-dotenv does not override existing variables. Defining blank provider
# keys before importing app.config guarantees an offline run even when a local
# backend/.env exists.
for variable in ("QWEN_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
    os.environ[variable] = ""
os.environ["APP_MODE"] = "local"
os.environ["MEMORY_STORE"] = "sqlite"

sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings  # noqa: E402
from app.eval.ablation import AblationRunner  # noqa: E402
from app.eval.benchmark import BenchmarkRunner  # noqa: E402
from app.memory import MemoryOS  # noqa: E402


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


async def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="paper-eval-", dir=BACKEND_DIR) as temp:
        database = Path(temp) / "evaluation.db"
        settings = Settings(
            app_mode="local",
            qwen_api_key=None,
            qwen_chat_model="offline-not-used",
            qwen_embedding_model="offline-hashing",
            memory_store="sqlite",
            database_url=str(database),
            memory_token_budget=2500,
            retrieval_top_k=8,
        )
        memos = MemoryOS(settings)
        await memos.init()
        try:
            diagnostic = await BenchmarkRunner(memos).run()
            ablation = await AblationRunner(memos).run()
        finally:
            await memos.qwen.aclose()

    if diagnostic["provider_status"] != "offline":
        raise RuntimeError("Paper evaluation must run with the offline provider.")
    if diagnostic["provider_fallbacks"] != 0:
        raise RuntimeError("Unexpected provider fallback occurred during evaluation.")
    if diagnostic["chat_model"] != "offline-not-used":
        raise RuntimeError("Offline evaluation recorded an unexpected chat model.")
    if diagnostic["embedding_model"] != "offline-hashing":
        raise RuntimeError("Offline evaluation recorded an unexpected embedding model.")

    manifest: dict[str, Any] = {
        "artifact_version": 1,
        "mode": "deterministic offline",
        "num_scenarios": diagnostic["num_scenarios"],
        "retrieval_top_k": diagnostic["retrieval_top_k"],
        "memory_token_budget": diagnostic["memory_token_budget"],
        "evaluator": diagnostic["evaluator"],
        "reported_in_paper": {
            "context_recall": diagnostic["memory_recall_at_context"],
            "context_recall_hits": diagnostic["memory_recall_hits"],
            "context_recall_total": diagnostic["memory_recall_total"],
            "outdated_memory_errors": diagnostic["outdated_memory_errors"],
            "historical_context_reduction_percent": diagnostic[
                "token_savings_percent"
            ],
            "memory_context_tokens": diagnostic["memory_context_tokens"],
            "full_history_tokens": diagnostic["full_history_tokens"],
            "ablation": ablation["variants"],
        },
        "excluded_from_paper": {
            "offline_answer_accuracy": diagnostic["memory_agent_accuracy"],
            "offline_baseline_accuracy": diagnostic[
                "baseline_no_memory_accuracy"
            ],
            "reason": (
                "The deterministic fallback is a test double, not evidence "
                "about a language model."
            ),
        },
    }

    _write_json(output_dir / "diagnostic.json", diagnostic)
    _write_json(output_dir / "ablation.json", ablation)
    _write_json(output_dir / "manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    args = parser.parse_args()
    asyncio.run(generate(args.output_dir.resolve()))


if __name__ == "__main__":
    main()
