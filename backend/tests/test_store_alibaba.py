"""Regression coverage for the tenant-scoped Alibaba Tablestore adapter."""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.memory.store_alibaba import (
    _EVENTS_TABLE,
    _LEGACY_EVENTS_TABLE,
    _LEGACY_PRIMARY_TABLE,
    _PRIMARY_TABLE,
    AlibabaTablestoreMemoryStore,
    _attribute_value,
)
from app.models import MemoryRecord


def test_attribute_value_supports_tablestore_timestamp_tuples():
    columns = [
        ("data", '{"memory_id":"mem_1"}', 1721368000),
        ("user_id", "demo-user", 1721368000),
    ]

    assert _attribute_value(columns, "data") == '{"memory_id":"mem_1"}'
    assert _attribute_value(columns, "missing") is None


class _Row:
    def __init__(self, primary_key, attribute_columns=None):
        self.primary_key = primary_key
        self.attribute_columns = attribute_columns or []


class _TableMeta:
    def __init__(self, name, schema):
        self.table_name = name
        self.primary_key_schema = schema


class _FakeClient:
    def __init__(self):
        self.tables = {
            _LEGACY_PRIMARY_TABLE: {},
            _LEGACY_EVENTS_TABLE: {},
        }
        self.schemas = {}
        self.range_calls = []

    @staticmethod
    def _key(primary_key):
        return tuple((name, value) for name, value in primary_key)

    def list_table(self):
        return list(self.tables)

    def create_table(self, meta, _options, _throughput):
        self.tables[meta.table_name] = {}
        self.schemas[meta.table_name] = meta.primary_key_schema

    def put_row(self, table, row, _condition):
        self.tables[table][self._key(row.primary_key)] = row

    def get_row(self, table, primary_key, *_args):
        return None, self.tables[table].get(self._key(primary_key)), None

    def delete_row(self, table, row, _condition):
        self.tables[table].pop(self._key(row.primary_key), None)

    def get_range(self, table, _direction, start, _end, _columns, _limit):
        self.range_calls.append((table, start))
        rows = list(self.tables[table].values())
        first_name, first_value = start[0]
        if first_name == "tenant_id":
            rows = [
                row for row in rows
                if dict(row.primary_key).get("tenant_id") == first_value
            ]
            scope = start[1][1]
            if scope not in {_INF_MIN, _INF_MAX}:
                rows = [
                    row for row in rows
                    if dict(row.primary_key).get("project_scope") == scope
                ]
        return None, None, rows, None


_INF_MIN = object()
_INF_MAX = object()


@pytest.fixture
def fake_tablestore(monkeypatch):
    module = SimpleNamespace(
        INF_MIN=_INF_MIN,
        INF_MAX=_INF_MAX,
        Direction=SimpleNamespace(FORWARD="forward"),
        Row=_Row,
        TableMeta=_TableMeta,
        TableOptions=lambda: object(),
        ReservedThroughput=lambda value: value,
        CapacityUnit=lambda read, write: (read, write),
        Condition=lambda value: value,
        RowExistenceExpectation=SimpleNamespace(IGNORE="ignore"),
    )
    monkeypatch.setitem(sys.modules, "tablestore", module)
    return _FakeClient()


def _legacy_row(primary_key: str, payload: dict) -> _Row:
    return _Row(
        [("pk", primary_key)],
        [("data", json.dumps(payload), 1721368000)],
    )


@pytest.mark.asyncio
async def test_composite_schema_migrates_once_and_queries_only_tenant_range(
    fake_tablestore,
):
    first = MemoryRecord(
        memory_id="mem_a",
        user_id="tenant-a",
        project_id="project-a",
        session_id="s",
        content="tenant A memory",
    )
    other = MemoryRecord(
        memory_id="mem_b",
        user_id="tenant-b",
        project_id="project-a",
        session_id="s",
        content="tenant B memory",
    )
    fake_tablestore.tables[_LEGACY_PRIMARY_TABLE][(("pk", "mem_a"),)] = _legacy_row(
        "mem_a", json.loads(first.model_dump_json())
    )
    fake_tablestore.tables[_LEGACY_PRIMARY_TABLE][(("pk", "mem_b"),)] = _legacy_row(
        "mem_b", json.loads(other.model_dump_json())
    )
    fake_tablestore.tables[_LEGACY_EVENTS_TABLE][(("pk", "evt_a"),)] = _legacy_row(
        "evt_a",
        {
            "event_id": "evt_a",
            "user_id": "tenant-a",
            "project_id": "project-a",
            "kind": "created",
            "timestamp": "2026-07-19T00:00:00+00:00",
        },
    )

    store = AlibabaTablestoreMemoryStore(Settings())
    store._client = fake_tablestore
    await store.init()

    assert fake_tablestore.schemas[_PRIMARY_TABLE] == [
        ("tenant_id", "STRING"),
        ("project_scope", "STRING"),
        ("record_id", "STRING"),
    ]
    assert fake_tablestore.schemas[_EVENTS_TABLE] == [
        ("tenant_id", "STRING"),
        ("project_scope", "STRING"),
        ("record_id", "STRING"),
    ]

    fake_tablestore.range_calls.clear()
    records = await store.list("tenant-a", "project-a", include_all=True)
    assert [record.memory_id for record in records] == ["mem_a"]
    assert fake_tablestore.range_calls
    assert all(table == _PRIMARY_TABLE for table, _ in fake_tablestore.range_calls)
    assert all(start[0] == ("tenant_id", "tenant-a") for _, start in fake_tablestore.range_calls)

    # Direct reads use the lookup row; they do not scan any table.
    fake_tablestore.range_calls.clear()
    assert (await store.get("mem_a")).user_id == "tenant-a"
    assert fake_tablestore.range_calls == []

    # A second startup observes the durable marker and never rescans legacy data.
    await store.init()
    assert not any(
        table in {_LEGACY_PRIMARY_TABLE, _LEGACY_EVENTS_TABLE}
        for table, _ in fake_tablestore.range_calls
    )


@pytest.mark.asyncio
async def test_tablestore_delete_removes_composite_and_lookup_rows(fake_tablestore):
    store = AlibabaTablestoreMemoryStore(Settings())
    store._client = fake_tablestore
    await store.init()
    memory = MemoryRecord(
        memory_id="mem_delete",
        user_id="tenant-a",
        project_id="project-a",
        session_id="s",
        content="delete me",
    )
    await store.add(memory)
    assert await store.get(memory.memory_id) is not None

    await store.delete(memory.memory_id)

    assert await store.get(memory.memory_id) is None
    assert await store.list("tenant-a", "project-a", include_all=True) == []
