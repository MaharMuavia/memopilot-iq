"""MemoPilot IQ FastAPI application entrypoint.

Wires up CORS, logging, the MemoryOS engine, the OSS client and all routers.
Exposes a lifespan that initialises the memory store and optionally seeds the
scripted demo (set SEED_DEMO=1).
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .memory import MemoryOS
from .routes import (
    analytics as analytics_routes,
    chat,
    demo as demo_routes,
    eval as eval_routes,
    health,
    memories,
    reflection as reflection_routes,
    trace as trace_routes,
)
from .seed import seed_demo
from .storage.oss_client import OSSClient
from .utils.logging import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    memos = MemoryOS(settings)
    await memos.init()
    app.state.memos = memos
    app.state.oss = OSSClient(settings)
    app.state.last_eval_report = None
    app.state.last_traces = {}
    logger.info("MemoPilot IQ started in %s (store: %s, qwen: %s)",
                memos.mode, memos.store.backend_name, settings.qwen_configured)

    if os.getenv("SEED_DEMO", "0") == "1":
        await seed_demo(memos)
        logger.info("Demo data seeded.")

    yield
    await memos.qwen.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MemoPilot IQ",
        description="A self-improving persistent-memory agent (Qwen Cloud, Track 1: MemoryAgent).",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(memories.router)
    app.include_router(eval_routes.router)
    app.include_router(trace_routes.router)
    app.include_router(demo_routes.router)
    app.include_router(reflection_routes.router)
    app.include_router(analytics_routes.router)

    @app.get("/")
    async def root():
        return {"name": "MemoPilot IQ", "docs": "/docs", "health": "/health"}

    return app


app = create_app()
