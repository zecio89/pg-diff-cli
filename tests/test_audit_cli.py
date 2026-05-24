"""Tests for pg_diff_cli.audit_cli."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from pg_diff_cli.audit_cli import build_audit_parser, run_audit_cmd
from pg_diff_cli.audit_log import AuditEntry, append_entry, build_entry
from unittest.mock import MagicMock


def _make_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_audit_parser(sub)
    return parser


def _make_diff(added=0, removed=0, modified=0):
    diff = MagicMock()
    diff.added_tables = list(range(added))
    diff.removed_tables = list(range(removed))
    diff.modified_tables = list(range(modified))
    return diff


def test_build_audit_parser_registers_subcommands():
    parser = _make_parser()
    args = parser.parse_args(["audit", "list"])
    assert args.audit_cmd == "list"


def test_list_empty_log(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    parser = _make_parser()
    args = parser.parse_args(["audit", "list", "--log", str(log)])
    rc = run_audit_cmd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit entries" in out


def test_list_shows_entries(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    entry = build_entry("postgresql://src", "postgresql://tgt", _make_diff(added=2))
    append_entry(entry, log_path=log)
    parser = _make_parser()
    args = parser.parse_args(["audit", "list", "--log", str(log)])
    rc = run_audit_cmd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "CHANGED" in out


def test_list_changed_only_filter(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    noop = build_entry("src", "tgt", _make_diff())
    changed = build_entry("src", "tgt", _make_diff(added=1))
    append_entry(noop, log_path=log)
    append_entry(changed, log_path=log)
    parser = _make_parser()
    args = parser.parse_args(["audit", "list", "--log", str(log), "--changed-only"])
    rc = run_audit_cmd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 audit log entry" in out


def test_clear_nonexistent_log(tmp_path, capsys):
    log = tmp_path / "missing.jsonl"
    parser = _make_parser()
    args = parser.parse_args(["audit", "clear", "--log", str(log), "--yes"])
    rc = run_audit_cmd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "does not exist" in out


def test_clear_deletes_file(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    entry = build_entry("src", "tgt", _make_diff())
    append_entry(entry, log_path=log)
    assert log.exists()
    parser = _make_parser()
    args = parser.parse_args(["audit", "clear", "--log", str(log), "--yes"])
    rc = run_audit_cmd(args)
    assert rc == 0
    assert not log.exists()


def test_clear_aborts_without_yes(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    log.write_text("{\"timestamp\": \"x\"}\n")
    parser = _make_parser()
    args = parser.parse_args(["audit", "clear", "--log", str(log)])
    with patch("builtins.input", return_value="n"):
        rc = run_audit_cmd(args)
    assert rc == 1
    assert log.exists()
