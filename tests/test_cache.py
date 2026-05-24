"""Tests for pg_diff_cli.cache."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pg_diff_cli.cache import (
    clear_cache,
    invalidate_cache,
    load_cached_schema,
    save_cached_schema,
)
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=None)


def _table(name: str) -> TableSchema:
    return TableSchema(name=name, columns=[_col("id", "integer", False)])


def _schema() -> DatabaseSchema:
    return DatabaseSchema(tables={"users": _table("users")})


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_save_creates_json_file(tmp_path: Path) -> None:
    db = _schema()
    path = save_cached_schema("dsn://x", "public", db, cache_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".json"


def test_load_returns_none_when_no_file(tmp_path: Path) -> None:
    result = load_cached_schema("dsn://x", "public", cache_dir=tmp_path)
    assert result is None


def test_roundtrip(tmp_path: Path) -> None:
    db = _schema()
    save_cached_schema("dsn://x", "public", db, cache_dir=tmp_path)
    loaded = load_cached_schema("dsn://x", "public", ttl=300, cache_dir=tmp_path)
    assert loaded is not None
    assert "users" in loaded.tables


def test_expired_entry_returns_none(tmp_path: Path) -> None:
    db = _schema()
    save_cached_schema("dsn://x", "public", db, cache_dir=tmp_path)
    # Force the timestamp to be very old
    cache_files = list(tmp_path.glob("*.json"))
    data = json.loads(cache_files[0].read_text())
    data["timestamp"] = time.time() - 9999
    cache_files[0].write_text(json.dumps(data))
    result = load_cached_schema("dsn://x", "public", ttl=300, cache_dir=tmp_path)
    assert result is None


def test_invalidate_removes_file(tmp_path: Path) -> None:
    db = _schema()
    save_cached_schema("dsn://x", "public", db, cache_dir=tmp_path)
    removed = invalidate_cache("dsn://x", "public", cache_dir=tmp_path)
    assert removed is True
    assert load_cached_schema("dsn://x", "public", cache_dir=tmp_path) is None


def test_invalidate_missing_returns_false(tmp_path: Path) -> None:
    assert invalidate_cache("dsn://x", "public", cache_dir=tmp_path) is False


def test_clear_removes_all(tmp_path: Path) -> None:
    db = _schema()
    save_cached_schema("dsn://a", "public", db, cache_dir=tmp_path)
    save_cached_schema("dsn://b", "public", db, cache_dir=tmp_path)
    count = clear_cache(tmp_path)
    assert count == 2
    assert list(tmp_path.glob("*.json")) == []


def test_clear_empty_dir_returns_zero(tmp_path: Path) -> None:
    assert clear_cache(tmp_path) == 0


def test_different_dsns_produce_different_files(tmp_path: Path) -> None:
    db = _schema()
    p1 = save_cached_schema("dsn://a", "public", db, cache_dir=tmp_path)
    p2 = save_cached_schema("dsn://b", "public", db, cache_dir=tmp_path)
    assert p1 != p2
