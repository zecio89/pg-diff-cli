"""Unit tests for pg_diff_cli.drift_detector."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.snapshot import save_snapshot
from pg_diff_cli.drift_detector import detect_drift, DriftResult


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=None)


def _table(name: str, cols: list) -> TableSchema:
    return TableSchema(name=name, columns=cols)


def _schema(*tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables={t.name: t for t in tables})


def _save(schema: DatabaseSchema) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    save_snapshot(schema, tmp.name)
    return tmp.name


def test_no_drift_when_schemas_identical():
    s = _schema(_table("users", [_col("id", "int")]))
    path = _save(s)
    try:
        result = detect_drift(s, path, baseline_name="v1")
        assert not result.has_drift
        assert result.changed_tables == 0
        assert "No drift" in result.summary()
    finally:
        os.unlink(path)


def test_drift_detected_on_added_table():
    baseline = _schema(_table("users", [_col("id", "int")]))
    live = _schema(
        _table("users", [_col("id", "int")]),
        _table("orders", [_col("id", "int")]),
    )
    path = _save(baseline)
    try:
        result = detect_drift(live, path, baseline_name="v1")
        assert result.has_drift
        assert result.changed_tables >= 1
        assert "Drift detected" in result.summary()
    finally:
        os.unlink(path)


def test_drift_detected_on_removed_table():
    baseline = _schema(
        _table("users", [_col("id", "int")]),
        _table("orders", [_col("id", "int")]),
    )
    live = _schema(_table("users", [_col("id", "int")]))
    path = _save(baseline)
    try:
        result = detect_drift(live, path)
        assert result.has_drift
    finally:
        os.unlink(path)


def test_missing_snapshot_raises_file_not_found():
    s = _schema(_table("users", [_col("id", "int")]))
    with pytest.raises(FileNotFoundError):
        detect_drift(s, "/nonexistent/path/snap.json")


def test_drift_result_table_count_reflects_live_schema():
    baseline = _schema(_table("a", [_col("x")]))
    live = _schema(_table("a", [_col("x")]), _table("b", [_col("y")]))
    path = _save(baseline)
    try:
        result = detect_drift(live, path)
        assert result.table_count == 2
    finally:
        os.unlink(path)
