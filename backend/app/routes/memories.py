"""Memory CRUD, timeline, controls and extraction endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from ..models import (
    CreateMemoryRequest,
    ExtractRequest,
    MemoryRecord,
    MemoryStatus,
    UpdateMemoryRequest,
)
from ..utils.security import contains_secret, redact_secrets

router = APIRouter(prefix="/api", tags=["memories"])


@router.get("/memories")
async def list_memories(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
    include_all: bool = False,
):
    memos = request.app.state.memos
    records = await memos.store.list(user_id, project_id, include_all=include_all)
    records.sort(key=lambda m: m.updated_at, reverse=True)
    return {"memories": [m.public_view() for m in records], "count": len(records)}


@router.get("/memories/timeline")
async def timeline(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    events = await memos.store.list_events(user_id, project_id)
    return {"events": events, "count": len(events)}


@router.post("/memories")
async def create_memory(req: CreateMemoryRequest, request: Request):
    memos = request.app.state.memos
    if contains_secret(req.content):
        raise HTTPException(status_code=400, detail="Refusing to store secret-like content.")
    record = MemoryRecord(
        user_id=req.user_id,
        project_id=req.project_id,
        session_id=req.session_id,
        type=req.type,
        content=redact_secrets(req.content),
        summary=req.summary or req.content[:80],
        importance=req.importance,
        confidence=req.confidence,
        tags=req.tags,
        is_critical=req.is_critical,
        privacy_level=req.privacy_level,
        expires_at=req.expires_at,
        reason=req.reason,
    )
    record.embedding = await memos.qwen.embed(record.content)
    await memos.store.add(record)
    await memos.store.add_event(
        {
            "user_id": req.user_id,
            "project_id": req.project_id,
            "kind": "created",
            "memory_id": record.memory_id,
            "type": record.type.value,
            "content": record.content,
            "reason": "Created manually via API.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return record.public_view()


@router.patch("/memories/{memory_id}")
async def update_memory(memory_id: str, req: UpdateMemoryRequest, request: Request):
    memos = request.app.state.memos
    mem = await memos.store.get(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found.")

    if req.pin:
        mem.status = MemoryStatus.pinned
        mem.is_critical = True
    if req.archive:
        mem.status = MemoryStatus.archived
    if req.status is not None:
        mem.status = req.status
    if req.content is not None:
        if contains_secret(req.content):
            raise HTTPException(status_code=400, detail="Refusing to store secret-like content.")
        mem.content = redact_secrets(req.content)
    if req.summary is not None:
        mem.summary = req.summary
    if req.importance is not None:
        mem.importance = req.importance
    if req.is_critical is not None:
        mem.is_critical = req.is_critical
    if req.tags is not None:
        mem.tags = req.tags

    mem.updated_at = datetime.now(timezone.utc)
    await memos.store.update(mem)
    await memos.store.add_event(
        {
            "user_id": mem.user_id,
            "project_id": mem.project_id,
            "kind": mem.status.value,
            "memory_id": mem.memory_id,
            "type": mem.type.value,
            "content": mem.content,
            "reason": "Updated via memory controls.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return mem.public_view()


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, request: Request, hard: bool = False):
    """Delete a memory. By default this is a soft delete (status=deleted);
    pass ``hard=true`` to remove the row entirely (explicit user action)."""
    memos = request.app.state.memos
    mem = await memos.store.get(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found.")
    if hard:
        await memos.store.delete(memory_id)
    else:
        mem.status = MemoryStatus.deleted
        mem.updated_at = datetime.now(timezone.utc)
        await memos.store.update(mem)
    await memos.store.add_event(
        {
            "user_id": mem.user_id,
            "project_id": mem.project_id,
            "kind": "deleted",
            "memory_id": memory_id,
            "type": mem.type.value,
            "content": mem.content,
            "reason": "Deleted by user." + (" (hard delete)" if hard else ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {"deleted": memory_id, "hard": hard}


@router.post("/memories/forget-all")
async def forget_all(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    count = await memos.store.clear_user(user_id, project_id)
    await memos.store.add_event(
        {
            "user_id": user_id,
            "project_id": project_id,
            "kind": "deleted",
            "memory_id": "*",
            "type": "deleted_by_user",
            "content": f"Forget-all removed {count} memories.",
            "reason": "User requested forget all.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {"forgotten": count}


@router.get("/memories/export")
async def export_memories(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    records = await memos.store.list(user_id, project_id, include_all=True)
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "project_id": project_id,
        "memories": [m.public_view() for m in records],
    }


@router.post("/memory/extract")
async def extract(req: ExtractRequest, request: Request):
    """Run extraction manually (for testing the pipeline)."""
    memos = request.app.state.memos
    actions = await memos.remember(
        user_id=req.user_id,
        project_id=req.project_id,
        session_id=req.session_id,
        message=req.message,
    )
    return actions.model_dump()
