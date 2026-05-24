"""Tests for pg_diff_cli.checksum."""

from __future__ import annotations

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.checksum import (
    checksum_schema,
    checksum_table,
    checksums_match,
    checksum_report,
)


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable)


def _table(name: str, cols: list[TableColumn] | None = None) -> TableSchema:
    return TableSchema(name=name, columns=cols or [])


def _schema(*tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# checksum_table
# ---------------------------------------------------------------------------

def test_checksum_table_is_hex_string():
    tbl = _table("users", [_col("id", "integer", False), _col("email")])
    result = checksum_table(tbl)
    assert isinstance(result, str)
    assert len(result) == 32  # MD5 hex length


def test_checksum_table_same_structure_same_hash():
    t1 = _table("users", [_col("id", "integer", False), _col("email")])
    t2 = _table("users", [_col("email"), _col("id", "integer", False)])
    # column order should not matter
    assert checksum_table(t1) == checksum_table(t2)


def test_checksum_table_different_type_different_hash():
    t1 = _table("users", [_col("id", "integer")])
    t2 = _table("users", [_col("id", "bigint")])
    assert checksum_table(t1) != checksum_table(t2)


# ---------------------------------------------------------------------------
# checksum_schema
# ---------------------------------------------------------------------------

def test_checksum_schema_is_sha256_hex():
    schema = _schema(_table("users", [_col("id", "integer")]))
    result = checksum_schema(schema)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex length


def test_checksum_schema_empty_is_stable():
    s1 = _schema()
    s2 = _schema()
    assert checksum_schema(s1) == checksum_schema(s2)


def test_checksum_schema_table_order_independent():
    s1 = _schema(_table("a", [_col("x")]), _table("b", [_col("y")]))
    s2 = _schema(_table("b", [_col("y")]), _table("a", [_col("x")]))
    assert checksum_schema(s1) == checksum_schema(s2)


# ---------------------------------------------------------------------------
# checksums_match
# ---------------------------------------------------------------------------

def test_checksums_match_identical_schemas():
    s = _schema(_table("orders", [_col("id", "integer")]))
    assert checksums_match(s, s) is True


def test_checksums_match_returns_false_when_different():
    s1 = _schema(_table("orders", [_col("id", "integer")]))
    s2 = _schema(_table("orders", [_col("id", "bigint")]))
    assert checksums_match(s1, s2) is False


# ---------------------------------------------------------------------------
# checksum_report
# ---------------------------------------------------------------------------

def test_checksum_report_contains_match_when_identical():
    s = _schema(_table("t", [_col("c")]))
    report = checksum_report(s, s)
    assert "MATCH" in report
    assert "MISMATCH" not in report


def test_checksum_report_contains_mismatch_when_different():
    s1 = _schema(_table("t", [_col("c", "text")]))
    s2 = _schema(_table("t", [_col("c", "varchar")]))
    report = checksum_report(s1, s2, source_label="prod", target_label="staging")
    assert "MISMATCH" in report
    assert "prod" in report
    assert "staging" in report
