"""Analytics + Memory Graph endpoints.

- GET /api/analytics : aggregate stats for the Analytics dashboard.
- GET /api/graph     : nodes + edges for the Live Memory Graph visualization.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from ..models import MemoryStatus
from ..utils.identity import effective_user_id

router = APIRouter(prefix="/api", tags=["analytics"])

_RETRIEVABLE = {MemoryStatus.active.value, MemoryStatus.pinned.value}
_VISIBLE = {
    MemoryStatus.active.value,
    MemoryStatus.pinned.value,
    MemoryStatus.superseded.value,
    MemoryStatus.archived.value,
    MemoryStatus.expired.value,
}


@router.get("/analytics")
async def analytics(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    user_id = effective_user_id(request, user_id)
    memories = await memos.store.list(user_id, project_id, include_all=True)
    events = await memos.store.list_events(user_id, project_id)

    type_counts = Counter(
        m.type.value for m in memories if m.status.value in _RETRIEVABLE
    )
    status_counts = Counter(m.status.value for m in memories)
    event_kind_counts = Counter(e.get("kind", "unknown") for e in events)

    # Cumulative memory growth by day (from creation events / created_at).
    per_day: Dict[str, int] = defaultdict(int)
    for m in memories:
        day = str(m.created_at)[:10]
        per_day[day] += 1
    growth = [
        {"date": day, "count": per_day[day]} for day in sorted(per_day.keys())
    ]
    cumulative = 0
    for point in growth:
        cumulative += point["count"]
        point["cumulative"] = cumulative

    report = getattr(request.app.state, "last_eval_report", None)
    token_savings = report.get("token_savings_percent") if report else None

    return {
        "totals": {
            "total": len(memories),
            "active": sum(1 for m in memories if m.status.value in _RETRIEVABLE),
            "superseded": status_counts.get("superseded", 0),
            "expired": status_counts.get("expired", 0),
            "archived": status_counts.get("archived", 0),
            "critical": sum(1 for m in memories if m.is_critical),
        },
        "type_counts": dict(type_counts),
        "status_counts": dict(status_counts),
        "event_kind_counts": dict(event_kind_counts),
        "growth": growth,
        "token_savings_percent": token_savings,
        "total_events": len(events),
    }


@router.get("/graph")
async def graph(
    request: Request,
    user_id: str = "demo-user",
    project_id: str | None = "qwen-memoryagent",
):
    memos = request.app.state.memos
    user_id = effective_user_id(request, user_id)
    memories = await memos.store.list(user_id, project_id, include_all=True)
    visible = [m for m in memories if m.status.value in _VISIBLE]

    nodes: List[Dict[str, Any]] = [
        {
            "id": m.memory_id,
            "label": (m.summary or m.content)[:48],
            "type": m.type.value,
            "status": m.status.value,
            "is_critical": m.is_critical,
            "importance": round(m.importance, 3),
            "is_insight": "insight" in m.tags,
            "tags": m.tags,
        }
        for m in visible
    ]
    node_ids = {m.memory_id for m in visible}

    edges: List[Dict[str, str]] = []
    # Supersession edges (old -> new).
    for m in visible:
        if m.superseded_by and m.superseded_by in node_ids:
            edges.append({"source": m.memory_id, "target": m.superseded_by, "kind": "supersedes"})

    # Related edges via shared tags (deduplicated, capped to keep it readable).
    by_tag: Dict[str, List[str]] = defaultdict(list)
    for m in visible:
        for tag in m.tags:
            by_tag[tag].append(m.memory_id)
    seen_pairs = set()
    for tag, ids in by_tag.items():
        if len(ids) < 2 or len(ids) > 8:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pair = tuple(sorted((ids[i], ids[j])))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                edges.append({"source": pair[0], "target": pair[1], "kind": "related"})
                if len(edges) > 120:
                    break

    return {"nodes": nodes, "edges": edges}
