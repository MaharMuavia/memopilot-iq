"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    settings = get_settings()
    memos = request.app.state.memos
    return {
        "status": "ok",
        "app": "MemoPilot IQ",
        "service": "MemoPilot IQ",
        "mode": memos.mode,
        "qwen_configured": settings.qwen_configured,
        "qwen_provider_status": memos.qwen.provider_status,
        "qwen_model": settings.qwen_chat_model,
        "memory_store": memos.store.backend_name,
        "alibaba_configured": settings.alibaba_configured,
        "oss_configured": settings.oss_configured,
        "token_budget": settings.memory_token_budget,
    }
