"""Alibaba Cloud Tablestore memory store.

Production rows use a tenant/project/record composite primary key.  That is
important for both cost and isolation: normal reads are bounded to one tenant
range instead of scanning every row in the instance and filtering in Python.

The first startup after this schema was introduced performs an idempotent,
one-time migration from the legacy single-key tables.  The legacy tables are
left intact as a rollback aid, but are never read by request paths after the
migration marker is written.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..config import Settings
from ..models import MemoryRecord
from ..utils.logging import get_logger
from .store_base import MemoryStore

logger = get_logger("store_alibaba")

_LEGACY_PRIMARY_TABLE = "memopilot_memories"
_LEGACY_EVENTS_TABLE = "memopilot_events"
_PRIMARY_TABLE = "memopilot_memories_v2"
_EVENTS_TABLE = "memopilot_events_v2"
_LOOKUP_TABLE = "memopilot_memory_lookup"
_META_TABLE = "memopilot_meta"
_MIGRATION_MARKER = "composite_schema_v2"
_GLOBAL_PROJECT_SCOPE = "0:global"


def _attribute_value(attribute_columns: Any, name: str) -> Any:
    """Return an attribute value across supported SDK row tuple shapes."""
    for column in attribute_columns or []:
        if len(column) >= 2 and column[0] == name:
            return column[1]
    return None


def _project_scope(project_id: Optional[str]) -> str:
    """Encode nullable project IDs without colliding with user project names."""
    return _GLOBAL_PROJECT_SCOPE if project_id is None else f"1:{project_id}"


class AlibabaTablestoreMemoryStore(MemoryStore):
    """Tenant-scoped Tablestore implementation using the official SDK."""

    schema_version = "composite-v2"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    @property
    def backend_name(self) -> str:
        return "alibaba-tablestore"

    def _ots(self):
        if self._client is None:
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
            CapacityUnit,
            ReservedThroughput,
            TableMeta,
            TableOptions,
        )

        client = self._ots()
        existing = set(client.list_table())
        schemas: Dict[str, List[Tuple[str, str]]] = {
            _PRIMARY_TABLE: [
                ("tenant_id", "STRING"),
                ("project_scope", "STRING"),
                ("record_id", "STRING"),
            ],
            _EVENTS_TABLE: [
                ("tenant_id", "STRING"),
                ("project_scope", "STRING"),
                ("record_id", "STRING"),
            ],
            _LOOKUP_TABLE: [("memory_id", "STRING")],
            _META_TABLE: [("pk", "STRING")],
        }
        for table, schema in schemas.items():
            if table in existing:
                continue
            client.create_table(
                TableMeta(table, schema),
                TableOptions(),
                ReservedThroughput(CapacityUnit(0, 0)),
            )
            existing.add(table)
            logger.info("Created Tablestore table %s", table)

        self._migrate_legacy_sync(existing)

    def _put_single_row(
        self,
        table: str,
        primary_key: Sequence[Tuple[str, Any]],
        payload: Dict[str, Any],
    ) -> None:
        from tablestore import Condition, Row, RowExistenceExpectation  # type: ignore

        attributes = [("data", json.dumps(payload, default=str))]
        self._ots().put_row(
            table,
            Row(list(primary_key), attributes),
            Condition(RowExistenceExpectation.IGNORE),
        )

    def _put_entity_row(
        self,
        table: str,
        user_id: str,
        project_id: Optional[str],
        record_id: str,
        payload: Dict[str, Any],
    ) -> None:
        from tablestore import Condition, Row, RowExistenceExpectation  # type: ignore

        primary_key = [
            ("tenant_id", user_id),
            ("project_scope", _project_scope(project_id)),
            ("record_id", record_id),
        ]
        attributes: List[Tuple[str, Any]] = [
            ("data", json.dumps(payload, default=str)),
            ("user_id", user_id),
            ("project_id", project_id or ""),
        ]
        # These fields remain visible to a future SearchIndex without changing
        # the durable JSON record used by the rest of the application.
        for key in ("status", "type", "updated_at", "importance", "kind", "timestamp"):
            value = payload.get(key)
            if value is not None:
                attributes.append((key, value if isinstance(value, (int, float)) else str(value)))
        self._ots().put_row(
            table,
            Row(primary_key, attributes),
            Condition(RowExistenceExpectation.IGNORE),
        )

    def _put_memory_sync(self, memory: MemoryRecord) -> None:
        payload = json.loads(memory.model_dump_json())
        self._put_entity_row(
            _PRIMARY_TABLE,
            memory.user_id,
            memory.project_id,
            memory.memory_id,
            payload,
        )
        # The lookup table preserves the existing get(memory_id) contract
        # without any scan. API and extraction layers still enforce ownership.
        self._put_single_row(
            _LOOKUP_TABLE,
            [("memory_id", memory.memory_id)],
            payload,
        )

    def _get_payload(
        self, table: str, primary_key: Sequence[Tuple[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        _, row, _ = self._ots().get_row(table, list(primary_key), [], None, 1)
        if not row:
            return None
        data = _attribute_value(row.attribute_columns, "data")
        return json.loads(data) if data else None

    def _range_payloads(
        self, table: str, user_id: str, project_id: Optional[str], all_projects: bool
    ) -> List[Dict[str, Any]]:
        from tablestore import Direction, INF_MAX, INF_MIN  # type: ignore

        if all_projects:
            start = [
                ("tenant_id", user_id),
                ("project_scope", INF_MIN),
                ("record_id", INF_MIN),
            ]
            end = [
                ("tenant_id", user_id),
                ("project_scope", INF_MAX),
                ("record_id", INF_MAX),
            ]
        else:
            scope = _project_scope(project_id)
            start = [
                ("tenant_id", user_id),
                ("project_scope", scope),
                ("record_id", INF_MIN),
            ]
            end = [
                ("tenant_id", user_id),
                ("project_scope", scope),
                ("record_id", INF_MAX),
            ]

        output: List[Dict[str, Any]] = []
        while start:
            _, next_start, rows, _ = self._ots().get_range(
                table, Direction.FORWARD, start, end, [], 5000
            )
            for row in rows:
                data = _attribute_value(row.attribute_columns, "data")
                if data:
                    output.append(json.loads(data))
            start = next_start
        return output

    def _legacy_scan(self, table: str) -> List[Dict[str, Any]]:
        """Full scan used only by the one-time schema migration."""
        from tablestore import Direction, INF_MAX, INF_MIN  # type: ignore

        start = [("pk", INF_MIN)]
        end = [("pk", INF_MAX)]
        output: List[Dict[str, Any]] = []
        while start:
            _, next_start, rows, _ = self._ots().get_range(
                table, Direction.FORWARD, start, end, [], 5000
            )
            for row in rows:
                data = _attribute_value(row.attribute_columns, "data")
                if data:
                    output.append(json.loads(data))
            start = next_start
        return output

    def _migrate_legacy_sync(self, existing: set[str]) -> None:
        if self._get_payload(_META_TABLE, [("pk", _MIGRATION_MARKER)]):
            return

        migrated_memories = 0
        migrated_events = 0
        if _LEGACY_PRIMARY_TABLE in existing:
            for payload in self._legacy_scan(_LEGACY_PRIMARY_TABLE):
                memory = MemoryRecord.model_validate(payload)
                self._put_memory_sync(memory)
                migrated_memories += 1
        if _LEGACY_EVENTS_TABLE in existing:
            for payload in self._legacy_scan(_LEGACY_EVENTS_TABLE):
                event_id = str(payload.get("event_id") or f"evt_{uuid.uuid4().hex}")
                payload = {**payload, "event_id": event_id}
                user_id = str(payload.get("user_id") or "")
                if not user_id:
                    logger.warning("Skipping legacy event without user_id")
                    continue
                self._put_entity_row(
                    _EVENTS_TABLE,
                    user_id,
                    payload.get("project_id"),
                    event_id,
                    payload,
                )
                migrated_events += 1

        self._put_single_row(
            _META_TABLE,
            [("pk", _MIGRATION_MARKER)],
            {
                "schema": self.schema_version,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "memories": migrated_memories,
                "events": migrated_events,
            },
        )
        logger.info(
            "Tablestore composite-key migration complete: %d memories, %d events",
            migrated_memories,
            migrated_events,
        )

    async def add(self, memory: MemoryRecord) -> MemoryRecord:
        await asyncio.to_thread(self._put_memory_sync, memory)
        return memory

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        payload = await asyncio.to_thread(
            self._get_payload, _LOOKUP_TABLE, [("memory_id", memory_id)]
        )
        return MemoryRecord.model_validate(payload) if payload else None

    async def update(self, memory: MemoryRecord) -> MemoryRecord:
        return await self.add(memory)

    def _delete_row(
        self, table: str, primary_key: Sequence[Tuple[str, Any]]
    ) -> None:
        from tablestore import Condition, Row, RowExistenceExpectation  # type: ignore

        self._ots().delete_row(
            table,
            Row(list(primary_key)),
            Condition(RowExistenceExpectation.IGNORE),
        )

    async def delete(self, memory_id: str) -> None:
        memory = await self.get(memory_id)
        if memory is None:
            return
        await asyncio.to_thread(
            self._delete_row,
            _PRIMARY_TABLE,
            [
                ("tenant_id", memory.user_id),
                ("project_scope", _project_scope(memory.project_id)),
                ("record_id", memory.memory_id),
            ],
        )
        await asyncio.to_thread(
            self._delete_row, _LOOKUP_TABLE, [("memory_id", memory.memory_id)]
        )

    async def list(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        include_all: bool = False,
    ) -> List[MemoryRecord]:
        if project_id is None:
            rows = await asyncio.to_thread(
                self._range_payloads, _PRIMARY_TABLE, user_id, None, True
            )
        else:
            project_rows = await asyncio.to_thread(
                self._range_payloads, _PRIMARY_TABLE, user_id, project_id, False
            )
            global_rows = await asyncio.to_thread(
                self._range_payloads, _PRIMARY_TABLE, user_id, None, False
            )
            rows = [*project_rows, *global_rows]

        records = [MemoryRecord.model_validate(row) for row in rows]
        if include_all:
            return records
        if statuses:
            return [memory for memory in records if memory.status.value in statuses]
        return records

    async def add_event(self, event: Dict[str, Any]) -> None:
        timestamp = str(event.get("timestamp") or datetime.now(timezone.utc).isoformat())
        event_id = f"{timestamp}|evt_{uuid.uuid4().hex}"
        payload = {**event, "event_id": event_id, "timestamp": timestamp}
        user_id = str(payload.get("user_id") or "")
        if not user_id:
            raise ValueError("Tablestore events require user_id")
        await asyncio.to_thread(
            self._put_entity_row,
            _EVENTS_TABLE,
            user_id,
            payload.get("project_id"),
            event_id,
            payload,
        )

    async def list_events(
        self, user_id: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if project_id is None:
            return await asyncio.to_thread(
                self._range_payloads, _EVENTS_TABLE, user_id, None, True
            )
        project_rows = await asyncio.to_thread(
            self._range_payloads, _EVENTS_TABLE, user_id, project_id, False
        )
        global_rows = await asyncio.to_thread(
            self._range_payloads, _EVENTS_TABLE, user_id, None, False
        )
        return [*project_rows, *global_rows]

    async def clear_user(self, user_id: str, project_id: Optional[str] = None) -> int:
        records = await self.list(user_id, project_id, include_all=True)
        events = await self.list_events(user_id, project_id)
        for memory in records:
            await self.delete(memory.memory_id)
        for event in events:
            event_id = str(event.get("event_id") or "")
            if not event_id:
                continue
            await asyncio.to_thread(
                self._delete_row,
                _EVENTS_TABLE,
                [
                    ("tenant_id", user_id),
                    ("project_scope", _project_scope(event.get("project_id"))),
                    ("record_id", event_id),
                ],
            )
        return len(records)
