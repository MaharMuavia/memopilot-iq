"""Run MemoPilot IQ on the LoCoMo long-conversation memory benchmark.

Usage (from backend/):

    # 1) fetch the official dataset (not redistributed with this repo)
    python scripts/run_locomo.py --download

    # 2) fast, deterministic, model-independent memory-layer evaluation
    python scripts/run_locomo.py --retrieval-only

    # 3) full answer-level run with your live Qwen key in backend/.env
    python scripts/run_locomo.py --max-conversations 3 --max-qa 50

Flags: --mode verbatim|extract, --top-k N, --include-adversarial, --out FILE.
Results print as a table and are written to a JSON report.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "locomo10.json")


def download(dest: str) -> None:
    from app.eval.locomo import LOCOMO_URL

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading LoCoMo from {LOCOMO_URL} ...")
    urllib.request.urlretrieve(LOCOMO_URL, dest)
    print(f"Saved to {dest}")


async def main(args: argparse.Namespace) -> None:
    if args.top_k:
        os.environ["RETRIEVAL_TOP_K"] = str(args.top_k)
    if args.model:
        os.environ["QWEN_CHAT_MODEL"] = args.model
    os.environ.setdefault("DATABASE_URL", "sqlite:///./locomo_run.db")

    from app.config import get_settings
    get_settings.cache_clear()
    from app.eval.locomo import LoCoMoRunner
    from app.memory import MemoryOS

    settings = get_settings()
    memos = MemoryOS(settings)
    await memos.init()
    print(f"qwen_configured={settings.qwen_configured} "
          f"model={settings.qwen_chat_model} top_k={settings.retrieval_top_k}")

    checkpoint = None if args.retrieval_only else args.checkpoint
    if checkpoint and args.fresh and os.path.exists(checkpoint):
        os.remove(checkpoint)
        print(f"removed stale checkpoint {checkpoint}")

    report = await LoCoMoRunner(memos).run(
        args.path,
        mode=args.mode,
        max_conversations=args.max_conversations,
        max_qa_per_conversation=args.max_qa,
        include_adversarial=args.include_adversarial,
        retrieval_only=args.retrieval_only,
        checkpoint_path=checkpoint,
    )
    await memos.qwen.aclose()

    print(f"\n=== LoCoMo report ({report['mode']}, "
          f"{report['conversations']} conversations, "
          f"{report['turns_ingested']} turns, {report['elapsed_s']}s) ===")
    header = f"{'category':<14} {'n':>5} {'F1':>7} {'EM':>7} {'ev-recall':>10}"
    print(header)
    rows = list(report["by_category"].items()) + [("overall", report["overall"])]
    for cat, m in rows:
        ev = m.get("evidence_recall", "")
        print(f"{cat:<14} {m['n']:>5} {m['f1']:>7.3f} {m['exact_match']:>7.3f} {str(ev):>10}")

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nreport written to {args.out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--download", action="store_true", help="fetch the official dataset and exit")
    p.add_argument("--path", default=DATA_PATH)
    p.add_argument("--mode", choices=["verbatim", "extract"], default="verbatim")
    p.add_argument("--max-conversations", type=int, default=None)
    p.add_argument("--max-qa", type=int, default=None, help="max QA pairs per conversation")
    p.add_argument("--include-adversarial", action="store_true")
    p.add_argument("--retrieval-only", action="store_true",
                   help="skip answer generation; report evidence recall only")
    p.add_argument("--top-k", type=int, default=None, help="override RETRIEVAL_TOP_K")
    p.add_argument("--model", default=None, help="override QWEN_CHAT_MODEL for answering")
    p.add_argument("--checkpoint", default="locomo_checkpoint.json",
                   help="per-QA resume file for answer-level runs")
    p.add_argument("--fresh", action="store_true", help="discard any existing checkpoint")
    p.add_argument("--out", default="locomo_report.json")
    args = p.parse_args()

    if args.download:
        download(args.path)
    else:
        asyncio.run(main(args))
