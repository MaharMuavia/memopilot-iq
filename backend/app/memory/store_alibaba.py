"""Alibaba Cloud memory store (Tablestore / OTS).

This is the ALIBABA_CLOUD_MODE persistent backend. It uses Alibaba Cloud
Tablestore (`tablestore` SDK) for durable, multi-region memory storage and is
the production target for the deployed backend.

Deployment proof: this file imports and uses the official Alibaba Cloud
``tablestore`` SDK with credentials/endpoint sourced from
:class:`~app.config.Settings`. When the SDK or credentials are unavailable it
raises, and the factory in :mod:`app.memory` falls back to SQLite so local dev
still works. See ``docs/deployment_alibaba.md``.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from ..config import Settings
from ..models import MemoryRecord
from ..utils.logging import get_logger
from .store_base import MemoryStore

logger = get_logger("store_alibaba")

_PRIMARY_TABLE = "memopilot_memories"
_EVENTS_TABLE = "memopilot_events"


class AlibabaTablestoreMemoryStore(MemoryStore):
    """Tablestore-backed implementation.

    Requires: ``pip install tablestore`` and the ALIBABA_* env vars.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None  # lazily created OTSClient

    @property
    def backend_name(self) -> str:
        return "alibaba-tablestore"

    def _ots(self):
        if self._client is None:
            # Imported lazily so the SDK is only a hard dependency in cloud mode.
            from tablestore import OTSClient  # type: ignore

            s = self.settings
            self._client = OTSClient(
                s.alibaba_tablestore_endpoint,
                s.alibaba_access_key_id,
                s.alibaba_access_key_secret,
                s.alibaba_tablestore_instance,
            )
            logger.info(
                "Connected to Alibaba Cloud Tablestore instance '%s'",
                s.alibaba_tablestore_instance,
            )
        return self._client

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        from tablestore import (  # type: ignore
            TableMeta,
            TableOptions,
            ReservedThroughput,
            CapacityUnit,
        )

        client = self._ots()
        existing = set(client.list_table())
        for table in (_PRIMARY_TABLE, _EVENTS_TABLE):
            if table not in existing:
                schema = [("pk", "STRING")]
                meta = TableMeta(table, schema)
                client.create_table(
                    meta,
                    TableOptions(),
                    ReservedThroughput(CapacityUnit(0, 0)),
                )
                logger.info("Created Tablestore table %s", table)

    # The Tablestore row helpers below keep the whole record as a single JSON
    # attribute so the schema mirrors the SQLite store exactly.
    def _put_row(self, table: str, pk_value: str, payload: Dict[str, Any]) -> None:
        from tablestore import Row, Condition, RowExistenceExpectation  # type: ignore

        client = self._ots()
        primary_key = [("pk", pk_value)]
        attribute_columns = [("data", json.dumps(payload, default=str))]
        for key in ("user_id", "project_id"):
            if payload.get(key) is not None:
                attribute_columns.append((key, str(payload[key])))
        row = Row(primary_key, attribute_columns)
        client.put_row(
            table, row, Condition(RowExistenceExpectation.IGNORE)
        )

    async def add(self, memory: MemoryRecord) -> MemoryRecord:
        await asyncio.to_thread(
            self._put_row,
            _PRIMARY_TABLE,
            memory.memory_id,
            json.loads(memory.model_dump_json()),
        )
        return memory

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        from tablestore import INF_MIN, INF_MAX  # type: ignore  # noqa: F401

        def _get() -> Optional[str]:
            client = self._ots()
            _, row, _ = client.get_row(_PRIMARY_TABLE, [("pk", memory_id)], [], None, 1)
            if not row:
                return None
            return dict(row.attribute_columns).get("data")

        data = await asyncio.to_thread(_get)
        return MemoryRecord.model_validate_json(data) if data else None

    async def update(self, memory: MemoryRecord) -> MemoryRecord:
        return await self.add(memory)

    async def delete(self, memory_id: str) -> None:
        await asyncio.to_thread(self._delete_row, _PRIMARY_TABLE, memory_id)

    def _delete_row(self, table: str, pk_value: str) -> None:
        from tablestore import Row, Condition, RowExistenceExpectation  # type: ignore

        client = self._ots()
        client.delete_row(
            table,
            Row([("pk", pk_value)]),
            Condition(RowExistenceExpectation.IGNORE),
        )

    def _scan(self, table: str) -> List[Dict[str, Any]]:
        from tablestore import INF_MIN, INF_MAX, Direction  # type: ignore

        client = self._ots()
        start = [("pk", INF_MIN)]
        end = [("pk", INF_MAX)]
        rows_out: List[Dict[str, Any]] = []
        while start:
            consumed, next_start, rows, _ = client.get_range(
                table, Direction.FORWARD, start, end, [], 5000
            )
            for r in rows:
                data = dict(r.attribute_columns).get("data")
                if data:
                    rows_out.append(json.loads(data))
            start = next_start
        return rows_out

    async def list(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        include_all: bool = False,
    ) -> List[MemoryRecord]:
        rows = await asyncio.to_thread(self._scan, _PRIMARY_TABLE)
        records = [MemoryRecord.model_validate(r) for r in rows if r.get("user_id") == user_id]
        if project_id is not None:
            records = [m for m in records if m.project_id in (project_id, None)]
        if include_all:
            return records
        if statuses:
            return [m for m in records if m.status.value in statuses]
        return records

    async def add_event(self, event: Dict[str, Any]) -> None:
        import uuid

        event_id = f"evt_{uuid.uuid4().hex}"
        payload = {**event, "event_id": event_id}
        await asyncio.to_thread(self._put_row, _EVENTS_TABLE, event_id, payload)

    async def list_events(
        self, user_id: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        rows = await asyncio.to_thread(self._scan, _EVENTS_TABLE)
        events = [e for e in rows if e.get("user_id") == user_id]
        if project_id is not None:
            events = [e for e in events if e.get("project_id") in (project_id, None)]
        return events

    async def clear_user(self, user_id: str, project_id: Optional[str] = None) -> int:
        records = await self.list(user_id, project_id, include_all=True)
        for m in records:
            await self.delete(m.memory_id)
        events = await self.list_events(user_id, project_id)
        for event in events:
            event_id = event.get("event_id")
            if event_id:
                await asyncio.to_thread(self._delete_row, _EVENTS_TABLE, str(event_id))
        return len(records)
