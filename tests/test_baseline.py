"""Tests for pg_diff_cli.baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pg_diff_cli.baseline import (
    baseline_path,
    diff_against_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _col(name: str, data_type: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=data_type, nullable=nullable, default=None)


def _table(name: str, *cols: TableColumn) -> TableSchema:
    return TableSchema(name=name, columns=list(cols))


def _schema(*tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# baseline_path
# ---------------------------------------------------------------------------

def test_baseline_path_format(tmp_path: Path) -> None:
    p = baseline_path("v1", tmp_path)
    assert p == tmp_path / "v1.json"


# ---------------------------------------------------------------------------
# save_baseline / load_baseline
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path: Path) -> None:
    schema = _schema(_table("users", _col("id", "integer")))
    path = save_baseline(schema, "v1", tmp_path)
    assert path.exists()
    assert path.suffix == ".json"


def test_roundtrip(tmp_path: Path) -> None:
    schema = _schema(_table("orders", _col("id", "integer"), _col("total", "numeric")))
    save_baseline(schema, "prod", tmp_path)
    loaded = load_baseline("prod", tmp_path)
    assert loaded.tables.keys() == schema.tables.keys()
    assert loaded.tables["orders"].columns[0].name == "id"


def test_load_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_baseline("ghost", tmp_path)


# ---------------------------------------------------------------------------
# list_baselines
# ---------------------------------------------------------------------------

def test_list_empty_dir(tmp_path: Path) -> None:
    assert list_baselines(tmp_path) == []


def test_list_nonexistent_dir(tmp_path: Path) -> None:
    assert list_baselines(tmp_path / "nope") == []


def test_list_returns_entries(tmp_path: Path) -> None:
    schema = _schema()
    save_baseline(schema, "alpha", tmp_path)
    save_baseline(schema, "beta", tmp_path)
    entries = list_baselines(tmp_path)
    names = [e.name for e in entries]
    assert names == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# diff_against_baseline
# ---------------------------------------------------------------------------

def test_diff_no_changes(tmp_path: Path) -> None:
    schema = _schema(_table("users", _col("id", "integer")))
    save_baseline(schema, "v1", tmp_path)
    diff = diff_against_baseline(schema, "v1", tmp_path)
    assert diff.added_tables == {}
    assert diff.removed_tables == {}


def test_diff_detects_added_table(tmp_path: Path) -> None:
    old = _schema(_table("users", _col("id", "integer")))
    new = _schema(_table("users", _col("id", "integer")), _table("posts", _col("id", "integer")))
    save_baseline(old, "v1", tmp_path)
    diff = diff_against_baseline(new, "v1", tmp_path)
    assert "posts" in diff.added_tables
