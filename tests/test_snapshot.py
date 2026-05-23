"""Tests for pg_diff_cli.snapshot."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.snapshot import (
    schema_to_dict,
    schema_from_dict,
    save_snapshot,
    load_snapshot,
)


def _col(name: str, dtype: str = "text", nullable: bool = True, default=None) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, column_default=default)


def _table(name: str, *cols: TableColumn) -> TableSchema:
    return TableSchema(name=name, columns=list(cols))


def _schema(*tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables={t.name: t for t in tables})


def test_schema_to_dict_structure():
    schema = _schema(_table("users", _col("id", "integer", False), _col("email")))
    result = schema_to_dict(schema)
    assert "tables" in result
    assert "users" in result["tables"]
    cols = result["tables"]["users"]["columns"]
    assert len(cols) == 2
    assert cols[0]["name"] == "id"
    assert cols[0]["data_type"] == "integer"
    assert cols[0]["is_nullable"] is False


def test_schema_from_dict_roundtrip():
    original = _schema(
        _table("orders", _col("order_id", "bigint", False, "nextval('orders_seq')"), _col("total", "numeric"))
    )
    data = schema_to_dict(original)
    restored = schema_from_dict(data)
    assert set(restored.tables.keys()) == {"orders"}
    cols = restored.tables["orders"].columns
    assert cols[0].name == "order_id"
    assert cols[0].column_default == "nextval('orders_seq')"
    assert cols[1].name == "total"


def test_schema_from_dict_empty():
    schema = schema_from_dict({})
    assert schema.tables == {}


def test_save_and_load_snapshot(tmp_path: Path):
    schema = _schema(_table("products", _col("sku", "text", False), _col("price", "numeric")))
    snapshot_path = tmp_path / "snapshots" / "schema.json"
    save_snapshot(schema, snapshot_path)
    assert snapshot_path.exists()
    loaded = load_snapshot(snapshot_path)
    assert "products" in loaded.tables
    assert loaded.tables["products"].columns[0].name == "sku"


def test_save_snapshot_creates_parent_dirs(tmp_path: Path):
    schema = _schema()
    deep_path = tmp_path / "a" / "b" / "c" / "snap.json"
    save_snapshot(schema, deep_path)
    assert deep_path.exists()


def test_load_snapshot_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Snapshot file not found"):
        load_snapshot(tmp_path / "missing.json")


def test_save_snapshot_valid_json(tmp_path: Path):
    schema = _schema(_table("t", _col("c")))
    path = tmp_path / "snap.json"
    save_snapshot(schema, path)
    with path.open() as fh:
        data = json.load(fh)
    assert "tables" in data
