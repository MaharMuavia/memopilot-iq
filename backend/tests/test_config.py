"""Configuration regression tests for deployment-friendly defaults."""
from __future__ import annotations

from app.config import Settings
from app.memory import MemoryOS
from app.memory.store_sqlite import SQLiteMemoryStore


def test_blank_qwen_placeholders_keep_working_defaults(monkeypatch):
    monkeypatch.setenv("QWEN_BASE_URL", "")
    monkeypatch.setenv("QWEN_CHAT_MODEL", "  ")
    monkeypatch.setenv("QWEN_EMBEDDING_MODEL", "")

    settings = Settings()

    assert settings.qwen_base_url == (
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    assert settings.qwen_chat_model == "qwen-plus"
    assert settings.qwen_embedding_model == "text-embedding-v3"


def test_runtime_mode_reflects_actual_fallback_store(tmp_path):
    settings = Settings(
        app_mode="alibaba",
        memory_store="alibaba",
        alibaba_access_key_id="configured",
        alibaba_access_key_secret="configured",
        alibaba_tablestore_endpoint="https://invalid.example",
        alibaba_tablestore_instance="configured",
    )
    engine = MemoryOS(settings)
    assert engine.mode == "ALIBABA_CLOUD_MODE"

    engine.store = SQLiteMemoryStore(f"sqlite:///{tmp_path / 'fallback.db'}")
    assert engine.mode == "LOCAL_MODE"


def test_blank_credentials_and_invalid_numeric_values_are_safe(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "   ")
    monkeypatch.setenv("ALIBABA_ACCESS_KEY_ID", " ")
    monkeypatch.setenv("MEMORY_TOKEN_BUDGET", "not-a-number")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "0")
    monkeypatch.setenv("RETRIEVAL_MIN_SIMILARITY", "not-a-number")
    monkeypatch.setenv("RETRIEVAL_MIN_KEYWORD_OVERLAP", "1.5")
    monkeypatch.setenv("QWEN_REQUEST_TIMEOUT_SECONDS", "999")
    monkeypatch.setenv("QWEN_MAX_RETRIES", "99")
    monkeypatch.setenv("QWEN_ENABLE_THINKING", "not-a-boolean")
    monkeypatch.setenv("QWEN_MAX_OUTPUT_TOKENS", "99999")

    settings = Settings()

    assert settings.qwen_configured is False
    assert settings.alibaba_configured is False
    assert settings.memory_token_budget == 2500
    assert settings.retrieval_top_k == 8
    assert settings.retrieval_min_similarity == 0.62
    assert settings.retrieval_min_keyword_overlap == 0.20
    assert settings.qwen_request_timeout_seconds == 60.0
    assert settings.qwen_max_retries == 1
    assert settings.qwen_enable_thinking is False
    assert settings.qwen_max_output_tokens == 700
