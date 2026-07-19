"""MemoPilot IQ FastAPI application entrypoint.

Wires up CORS, logging, the MemoryOS engine, the OSS client and all routers.
Exposes a lifespan that initialises the memory store and optionally seeds the
scripted demo (set SEED_DEMO=1).
"""
from __future__ import annotations

import os
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from .utils.platform import install_platform

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    memos = MemoryOS(settings)
    try:
        await memos.init()
    except Exception as exc:  # cloud store misconfig must not crash every request
        logger.error("Memory store init failed (%s); falling back to local SQLite.", exc)
        from .memory.store_sqlite import SQLiteMemoryStore

        memos.store = SQLiteMemoryStore(settings.database_url)
        memos.retriever.store = memos.store
        memos.extractor.store = memos.store
        memos.forgetting.store = memos.store
        memos.reflection.store = memos.store
        await memos.store.init()
    app.state.memos = memos
    app.state.oss = OSSClient(settings)
    app.state.last_eval_report = eval_routes.load_persisted_report(
        settings.eval_report_path
    )
    app.state.last_traces = {}
    logger.info("MemoPilot IQ started in %s (store: %s, qwen: %s)",
                memos.mode, memos.store.backend_name, settings.qwen_configured)
    if not settings.qwen_configured:
        logger.warning("QWEN_API_KEY not set: running in deterministic OFFLINE fallback. "
                       "Answers are synthetic; add a key to backend/.env for live Qwen.")

    if os.getenv("SEED_DEMO", "0") == "1":
        await seed_demo(memos)
        logger.info("Demo data seeded.")

    yield
    await memos.qwen.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MemoPilot IQ",
        description="A self-curating persistent-memory agent (Qwen Cloud, Track 1: MemoryAgent).",
        version="1.0.0",
        lifespan=lifespan,
    )
    configured_origins = [
        origin.strip()
        for origin in settings.frontend_origin.split(",")
        if origin.strip()
    ]
    if "*" in configured_origins:
        allowed_origins = ["*"]
    else:
        allowed_origins = list(dict.fromkeys([
            *configured_origins,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        # The public anonymous identity cookie is same-origin in production.
        # Cross-origin callers use API keys, so CORS credentials stay disabled
        # and FRONTEND_ORIGIN=* remains standards-safe for local API testing.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_platform(app)  # API-key auth, rate limiting, /metrics

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Never leak a raw 500. Log the full traceback with a request id and
        return a clean, structured error the frontend can display."""
        request_id = uuid.uuid4().hex[:12]
        logger.error(
            "Unhandled error [%s] on %s %s\n%s",
            request_id, request.method, request.url.path,
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal error. The team has been notified.",
                "request_id": request_id,
                "hint": "Check the backend console for the full traceback under this request_id.",
            },
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
