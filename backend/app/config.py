"""Application configuration for MemoPilot IQ.

Loads settings from environment variables (and an optional .env file).
The app supports two runtime modes:

- LOCAL_MODE: SQLite metadata + local in-process vector store. Runs on a
  laptop with no cloud credentials.
- ALIBABA_CLOUD_MODE: Alibaba Cloud persistent store (Tablestore) + OSS for
  logs/snapshots. Activated automatically when the relevant env vars exist.

The mode is decided in :func:`Settings.resolved_mode` so the UI can display it.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:
    # Optional: load .env if python-dotenv is installed. Never required.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

from pydantic import BaseModel, Field


LOCAL_MODE = "LOCAL_MODE"
ALIBABA_CLOUD_MODE = "ALIBABA_CLOUD_MODE"


class Settings(BaseModel):
    """Strongly-typed view over the environment."""

    # NOTE: defaults use ``default_factory`` so environment variables are read
    # at instantiation time (not import time). This lets tests/process managers
    # override env vars and construct a fresh Settings() that reflects them.
    app_mode: str = Field(default_factory=lambda: os.getenv("APP_MODE", "local"))

    # --- Qwen Cloud ---
    qwen_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("QWEN_API_KEY") or None
    )
    qwen_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
    )
    qwen_chat_model: str = Field(
        default_factory=lambda: os.getenv("QWEN_CHAT_MODEL", "qwen-plus")
    )
    qwen_embedding_model: str = Field(
        default_factory=lambda: os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
    )

    # --- Alibaba Cloud ---
    alibaba_access_key_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_ACCESS_KEY_ID") or None
    )
    alibaba_access_key_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_ACCESS_KEY_SECRET") or None
    )
    alibaba_region: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_REGION") or None
    )
    alibaba_oss_bucket: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_OSS_BUCKET") or None
    )
    alibaba_oss_endpoint: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_OSS_ENDPOINT") or None
    )
    alibaba_tablestore_endpoint: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_TABLESTORE_ENDPOINT") or None
    )
    alibaba_tablestore_instance: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALIBABA_TABLESTORE_INSTANCE") or None
    )

    # --- Storage ---
    memory_store: str = Field(
        default_factory=lambda: os.getenv("MEMORY_STORE", "sqlite")
    )
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./memopilot.db")
    )

    # --- Web ---
    frontend_origin: str = Field(
        default_factory=lambda: os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    )

    # --- Context budget ---
    memory_token_budget: int = Field(
        default_factory=lambda: int(os.getenv("MEMORY_TOKEN_BUDGET", "2500"))
    )
    retrieval_top_k: int = Field(
        default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "8"))
    )

    @property
    def qwen_configured(self) -> bool:
        return bool(self.qwen_api_key)

    @property
    def alibaba_configured(self) -> bool:
        """True when enough Alibaba credentials exist to use cloud storage."""
        return bool(
            self.alibaba_access_key_id
            and self.alibaba_access_key_secret
            and self.alibaba_tablestore_endpoint
            and self.alibaba_tablestore_instance
        )

    @property
    def oss_configured(self) -> bool:
        return bool(
            self.alibaba_access_key_id
            and self.alibaba_access_key_secret
            and self.alibaba_oss_bucket
            and self.alibaba_oss_endpoint
        )

    def resolved_mode(self) -> str:
        """Decide which runtime mode the app is actually running in.

        ALIBABA_CLOUD_MODE requires the Alibaba persistent store to be
        configured. Otherwise we transparently fall back to LOCAL_MODE so the
        project always runs.
        """
        if self.memory_store == "alibaba" and self.alibaba_configured:
            return ALIBABA_CLOUD_MODE
        if self.app_mode.lower() in {"alibaba", "alibaba_cloud", "cloud"} and (
            self.alibaba_configured
        ):
            return ALIBABA_CLOUD_MODE
        return LOCAL_MODE


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor used across the app."""
    return Settings()
