"""Regression coverage for Alibaba Tablestore SDK row handling."""
from __future__ import annotations

from app.memory.store_alibaba import _attribute_value


def test_attribute_value_supports_tablestore_timestamp_tuples():
    columns = [
        ("data", '{"memory_id":"mem_1"}', 1721368000),
        ("user_id", "demo-user", 1721368000),
    ]

    assert _attribute_value(columns, "data") == '{"memory_id":"mem_1"}'
    assert _attribute_value(columns, "missing") is None
