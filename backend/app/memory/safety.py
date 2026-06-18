"""Privacy / Safety engine for MemoryOS.

Canonical entry point for secret detection and redaction used across MemoryOS.
The low-level regex patterns live in :mod:`app.utils.security`; this module
exposes a small :class:`SafetyEngine` facade that the extractor and routes use,
keeping the "never store secrets" policy in one named place.
"""
from __future__ import annotations

from typing import List

from ..utils.security import contains_secret, find_secrets, redact_secrets


class SafetyEngine:
    """Blocks/redacts secrets before any text becomes a persisted memory."""

    def detect(self, text: str) -> List[str]:
        """Return the names of secret patterns found in *text*."""
        return find_secrets(text)

    def has_secret(self, text: str) -> bool:
        return contains_secret(text)

    def redact(self, text: str) -> str:
        return redact_secrets(text)

    def safe_or_redacted(self, text: str) -> tuple[str, bool]:
        """Return ``(redacted_text, had_secret)``."""
        return self.redact(text), self.has_secret(text)


# Module-level singleton for convenience.
safety_engine = SafetyEngine()
