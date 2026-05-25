"""Tests for pg_diff_cli.schema_hasher."""

from __future__ import annotations

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.schema_hasher import (
    hash_table,
    hash_schema,
    diff_hashes,
    SchemaHash,
)


def _col(name: str, dtype: str = "text", nullable: bool = True, default=None) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=default)


def _table(name: str, *cols: TableColumn) -> TableSchema:
    return TableSchema(name=name, columns=list(cols))


def _schema(*tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables={t.name: t for t in tables})


def test_hash_table_returns_hex_string():
    t = _table("users", _col("id", "integer"), _col("email"))
    h = hash_table(t)
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex


def test_hash_table_same_structure_same_hash():
    t1 = _table("users", _col("id", "integer"), _col("email"))
    t2 = _table("users", _col("id", "integer"), _col("email"))
    assert hash_table(t1) == hash_table(t2)


def test_hash_table_different_type_different_hash():
    t1 = _table("users", _col("id", "integer"))
    t2 = _table("users", _col("id", "bigint"))
    assert hash_table(t1) != hash_table(t2)


def test_hash_table_column_order_independent():
    t1 = _table("users", _col("a"), _col("b"))
    t2 = _table("users", _col("b"), _col("a"))
    assert hash_table(t1) == hash_table(t2)


def test_hash_schema_overall_is_hex():
    s = _schema(_table("users", _col("id", "integer")))
    sh = hash_schema(s)
    assert len(sh.overall) == 64


def test_hash_schema_tables_keyed_by_name():
    t = _table("orders", _col("id", "integer"))
    s = _schema(t)
    sh = hash_schema(s)
    assert "orders" in sh.tables
    assert sh.tables["orders"] == hash_table(t)


def test_schema_hash_matches_identical():
    s = _schema(_table("a", _col("x")))
    h1 = hash_schema(s)
    h2 = hash_schema(s)
    assert h1.matches(h2)


def test_schema_hash_not_matches_after_change():
    s1 = _schema(_table("a", _col("x", "text")))
    s2 = _schema(_table("a", _col("x", "integer")))
    assert not hash_schema(s1).matches(hash_schema(s2))


def test_diff_hashes_returns_none_when_same():
    s = _schema(_table("a", _col("x")))
    assert diff_hashes(hash_schema(s), hash_schema(s)) is None


def test_diff_hashes_returns_changed_table_names():
    s1 = _schema(_table("a", _col("x", "text")), _table("b", _col("y")))
    s2 = _schema(_table("a", _col("x", "integer")), _table("b", _col("y")))
    changed = diff_hashes(hash_schema(s1), hash_schema(s2))
    assert changed == ["a"]


def test_diff_hashes_includes_added_and_removed_tables():
    s1 = _schema(_table("a", _col("x")))
    s2 = _schema(_table("b", _col("y")))
    changed = diff_hashes(hash_schema(s1), hash_schema(s2))
    assert set(changed) == {"a", "b"}
