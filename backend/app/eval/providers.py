"""Multi-backbone provider registry for the cross-model generalization study.

The MemoryOS layer (extraction, scoring, retrieval, budgeting) is held fixed;
only the answer-generating LLM is swapped. All three providers are called
through the same OpenAI-compatible Chat Completions interface:

  * Qwen   — Alibaba Cloud DashScope (the production / headline model)
  * OpenAI — api.openai.com
  * Gemini — Google's OpenAI-compatibility endpoint

A provider is included only when its API key is present in the environment, so
the benchmark degrades gracefully to whatever is configured (Qwen-only, or all
three). This is a *research* add-on; Qwen remains the system's default model.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from ..config import Settings
from ..utils.logging import get_logger

logger = get_logger("providers")


def configured_backbones(settings: Settings) -> List[Dict[str, str]]:
    """Return the list of answer-generating backbones available right now."""
    out: List[Dict[str, str]] = []

    # Qwen (primary). Always listed when configured; falls back to offline below.
    if settings.qwen_configured:
        out.append({
            "name": "qwen",
            "label": f"Qwen ({settings.qwen_chat_model})",
            "api_key": settings.qwen_api_key or "",
            "base_url": settings.qwen_base_url,
            "model": settings.qwen_chat_model,
        })

    if os.getenv("OPENAI_API_KEY"):
        out.append({
            "name": "openai",
            "label": f"OpenAI ({os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o')})",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
        })

    if os.getenv("GEMINI_API_KEY"):
        out.append({
            "name": "gemini",
            "label": f"Gemini ({os.getenv('GEMINI_CHAT_MODEL', 'gemini-2.0-flash')})",
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "base_url": os.getenv(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai",
            ),
            "model": os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash"),
        })

    return out


async def backbone_chat(
    provider: Dict[str, str], messages: List[Dict[str, str]], temperature: float = 0.2
) -> Optional[str]:
    """Call one provider's OpenAI-compatible chat endpoint, retrying on 429
    rate limits (common on free Gemini tiers). Returns None only after retries
    are exhausted."""
    import asyncio

    url = provider["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {"model": provider["model"], "messages": messages, "temperature": temperature}

    for attempt in range(4):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 429:
                    wait = 5 * (attempt + 1)  # 5s, 10s, 15s backoff
                    logger.warning("Backbone %s rate-limited; retrying in %ds", provider.get("name"), wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data: Dict[str, Any] = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("Backbone %s failed (attempt %d): %s", provider.get("name"), attempt + 1, exc)
            await asyncio.sleep(2)
    return None
