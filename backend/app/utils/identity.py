"""Request identity helpers.

When API-key protection is enabled, the API key—not a user-supplied query
parameter—defines the memory namespace. In open local-demo mode callers can
still use an explicit ``user_id`` to make the project easy to try.
"""
from __future__ import annotations

from fastapi import HTTPException, Request


def effective_user_id(request: Request, requested_user_id: str) -> str:
    """Return the authenticated namespace, or the requested demo namespace."""
    return getattr(request.state, "authenticated_user_id", None) or requested_user_id


def require_owned(memory, user_id: str):
    """Avoid leaking the existence of another tenant's memory by returning 404."""
    if memory is None or memory.user_id != user_id:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return memory


def trace_key(user_id: str, session_id: str) -> str:
    """Namespace process-local traces by tenant as well as session.

    Session identifiers are client supplied and are not globally unique. A
    composite key prevents two tenants using ``session-001`` from overwriting
    each other's diagnostic trace.
    """
    return f"{user_id}\x1f{session_id}"
