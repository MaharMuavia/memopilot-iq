"""Security helpers: secret detection and redaction.

MemoryOS must NEVER persist secrets (API keys, tokens, passwords). Before any
text is stored as a memory it is passed through :func:`redact_secrets`. We also
expose :func:`contains_secret` so the extraction pipeline can drop whole
memories that are predominantly credentials.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Patterns that look like secrets. Conservative but covers common cases.
_SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("dashscope_key", re.compile(r"sk-[A-Za-z0-9-]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("alibaba_access_key", re.compile(r"LTAI[0-9A-Za-z]{12,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("generic_secret_assign", re.compile(
        r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|access[_-]?key)\s*[:=]\s*[^\s]{6,}"
    )),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

_REDACTION = "[REDACTED_SECRET]"


def find_secrets(text: str) -> List[str]:
    """Return the names of secret patterns detected in *text*."""
    hits: List[str] = []
    for name, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(name)
    return hits


def contains_secret(text: str) -> bool:
    return bool(find_secrets(text))


def redact_secrets(text: str) -> str:
    """Replace any secret-looking substrings with a redaction marker."""
    redacted = text
    for _name, pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTION, redacted)
    return redacted
