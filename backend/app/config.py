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


def _env_or_default(name: str, default: str) -> str:
    """Treat a missing *or blank* environment variable as the default.

    This matters for ``.env.example``: users commonly copy it and fill only
    ``QWEN_API_KEY``. Blank URL/model placeholders must not replace working
    DashScope defaults with empty strings.
    """
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _optional_env(name: str) -> Optional[str]:
    """Return a trimmed optional value; whitespace-only means unconfigured."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def _positive_env_int(name: str, default: int) -> int:
    """Read a positive integer without letting a bad deployment env crash boot."""
    value = os.getenv(name)
    try:
        parsed = int(value.strip()) if value and value.strip() else default
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read a bounded integer without allowing bad env values to break boot."""
    value = os.getenv(name)
    try:
        parsed = int(value.strip()) if value and value.strip() else default
    except ValueError:
        return default
    return parsed if minimum <= parsed <= maximum else default


def _bounded_float(name: str, default: float, minimum: float, maximum: float) -> float:
    """Read a bounded float without allowing bad env values to break boot."""
    value = os.getenv(name)
    try:
        parsed = float(value.strip()) if value and value.strip() else default
    except ValueError:
        return default
    return parsed if minimum <= parsed <= maximum else default


def _unit_interval_env_float(name: str, default: float) -> float:
    """Read a float in [0, 1] without allowing bad env values to break boot."""
    value = os.getenv(name)
    try:
        parsed = float(value.strip()) if value and value.strip() else default
    except ValueError:
        return default
    return parsed if 0.0 <= parsed <= 1.0 else default


def _env_bool(name: str, default: bool) -> bool:
    """Read a conventional boolean value and fall back safely on typos."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class Settings(BaseModel):
    """Strongly-typed view over the environment."""

    # NOTE: defaults use ``default_factory`` so environment variables are read
    # at instantiation time (not import time). This lets tests/process managers
    # override env vars and construct a fresh Settings() that reflects them.
    app_mode: str = Field(default_factory=lambda: _env_or_default("APP_MODE", "local"))

    # --- Qwen Cloud ---
    qwen_api_key: Optional[str] = Field(
        default_factory=lambda: _optional_env("QWEN_API_KEY")
    )
    qwen_base_url: str = Field(
        default_factory=lambda: _env_or_default(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
    )
    qwen_chat_model: str = Field(
        default_factory=lambda: _env_or_default("QWEN_CHAT_MODEL", "qwen-plus")
    )
    qwen_embedding_model: str = Field(
        default_factory=lambda: _env_or_default("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
    )
    qwen_request_timeout_seconds: float = Field(
        default_factory=lambda: _bounded_float(
            "QWEN_REQUEST_TIMEOUT_SECONDS", 60.0, 1.0, 180.0
        ),
        gt=0.0,
        le=180.0,
    )
    qwen_max_retries: int = Field(
        default_factory=lambda: _bounded_int("QWEN_MAX_RETRIES", 1, 0, 3),
        ge=0,
        le=3,
    )
    qwen_enable_thinking: bool = Field(
        default_factory=lambda: _env_bool("QWEN_ENABLE_THINKING", False)
    )
    qwen_max_output_tokens: int = Field(
        default_factory=lambda: _bounded_int(
            "QWEN_MAX_OUTPUT_TOKENS", 700, 64, 4096
        ),
        ge=64,
        le=4096,
    )

    # --- Alibaba Cloud ---
    alibaba_access_key_id: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_ACCESS_KEY_ID")
    )
    alibaba_access_key_secret: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_ACCESS_KEY_SECRET")
    )
    alibaba_region: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_REGION")
    )
    alibaba_oss_bucket: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_OSS_BUCKET")
    )
    alibaba_oss_endpoint: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_OSS_ENDPOINT")
    )
    alibaba_tablestore_endpoint: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_TABLESTORE_ENDPOINT")
    )
    alibaba_tablestore_instance: Optional[str] = Field(
        default_factory=lambda: _optional_env("ALIBABA_TABLESTORE_INSTANCE")
    )

    # --- Storage ---
    memory_store: str = Field(
        default_factory=lambda: _env_or_default("MEMORY_STORE", "sqlite")
    )
    database_url: str = Field(
        default_factory=lambda: _env_or_default("DATABASE_URL", "sqlite:///./memopilot.db")
    )
    eval_report_path: Optional[str] = Field(
        default_factory=lambda: _optional_env("EVAL_REPORT_PATH")
    )

    # --- Web ---
    frontend_origin: str = Field(
        default_factory=lambda: _env_or_default("FRONTEND_ORIGIN", "http://localhost:5173")
    )
    public_demo_isolation: bool = Field(
        default_factory=lambda: _env_bool("MEMOPILOT_PUBLIC_DEMO_ISOLATION", False)
    )
    identity_secret: Optional[str] = Field(
        default_factory=lambda: _optional_env("MEMOPILOT_IDENTITY_SECRET")
    )
    app_build_sha: str = Field(
        default_factory=lambda: _env_or_default("APP_BUILD_SHA", "development")
    )

    # --- Context budget ---
    memory_token_budget: int = Field(
        default_factory=lambda: _positive_env_int("MEMORY_TOKEN_BUDGET", 2500)
    )
    retrieval_top_k: int = Field(
        default_factory=lambda: _positive_env_int("RETRIEVAL_TOP_K", 8)
    )
    retrieval_min_similarity: float = Field(
        default_factory=lambda: _unit_interval_env_float(
            "RETRIEVAL_MIN_SIMILARITY", 0.62
        ),
        ge=0.0,
        le=1.0,
    )
    retrieval_min_keyword_overlap: float = Field(
        default_factory=lambda: _unit_interval_env_float(
            "RETRIEVAL_MIN_KEYWORD_OVERLAP", 0.20
        ),
        ge=0.0,
        le=1.0,
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
