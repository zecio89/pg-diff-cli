"""Tests for pg_diff_cli.audit_log."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pg_diff_cli.audit_log import (
    AuditEntry,
    _redact_dsn,
    append_entry,
    build_entry,
    load_entries,
)


def _make_diff(added=0, removed=0, modified=0):
    diff = MagicMock()
    diff.added_tables = [f"t{i}" for i in range(added)]
    diff.removed_tables = [f"t{i}" for i in range(removed)]
    diff.modified_tables = [f"t{i}" for i in range(modified)]
    return diff


def test_redact_dsn_hides_password():
    dsn = "postgresql://user:s3cr3t@localhost/mydb"
    result = _redact_dsn(dsn)
    assert "s3cr3t" not in result
    assert "***" in result
    assert "user" in result


def test_redact_dsn_without_password_unchanged():
    dsn = "postgresql://localhost/mydb"
    result = _redact_dsn(dsn)
    assert result == dsn


def test_build_entry_counts_correctly():
    diff = _make_diff(added=2, removed=1, modified=3)
    entry = build_entry("postgresql://src/db", "postgresql://tgt/db", diff)
    assert entry.tables_added == 2
    assert entry.tables_removed == 1
    assert entry.tables_modified == 3
    assert entry.had_changes is True


def test_build_entry_no_changes():
    diff = _make_diff()
    entry = build_entry("postgresql://src/db", "postgresql://tgt/db", diff)
    assert entry.had_changes is False


def test_build_entry_redacts_dsns():
    diff = _make_diff()
    entry = build_entry("postgresql://u:pass@host/db", "postgresql://u:pass@host/db2", diff)
    assert "pass" not in entry.source_dsn
    assert "pass" not in entry.target_dsn


def test_build_entry_tags_and_output(tmp_path):
    diff = _make_diff(added=1)
    entry = build_entry("src", "tgt", diff, output_file="/tmp/out.sql", tags=["ci", "prod"])
    assert entry.output_file == "/tmp/out.sql"
    assert entry.tags == ["ci", "prod"]


def test_append_and_load_roundtrip(tmp_path):
    log = tmp_path / "audit.jsonl"
    diff = _make_diff(added=1, modified=2)
    entry = build_entry("postgresql://src", "postgresql://tgt", diff, tags=["test"])
    append_entry(entry, log_path=log)
    loaded = load_entries(log_path=log)
    assert len(loaded) == 1
    assert loaded[0].tables_added == 1
    assert loaded[0].tables_modified == 2
    assert loaded[0].tags == ["test"]


def test_load_entries_missing_file_returns_empty(tmp_path):
    log = tmp_path / "nonexistent.jsonl"
    assert load_entries(log_path=log) == []


def test_append_multiple_entries(tmp_path):
    log = tmp_path / "audit.jsonl"
    for i in range(3):
        diff = _make_diff(added=i)
        entry = build_entry("src", "tgt", diff)
        append_entry(entry, log_path=log)
    loaded = load_entries(log_path=log)
    assert len(loaded) == 3
    assert loaded[2].tables_added == 2


def test_entry_to_dict_and_from_dict():
    diff = _make_diff(removed=1)
    entry = build_entry("src", "tgt", diff, output_file="out.sql")
    d = entry.to_dict()
    restored = AuditEntry.from_dict(d)
    assert restored.tables_removed == entry.tables_removed
    assert restored.output_file == "out.sql"
    assert restored.timestamp == entry.timestamp
