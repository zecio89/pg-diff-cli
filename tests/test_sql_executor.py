"""Tests for sql_executor and executor_cli."""
from __future__ import annotations

import argparse
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pg_diff_cli.sql_executor import ExecutionResult, execute_sql
from pg_diff_cli.executor_cli import build_executor_parser, run_executor_cmd


# ---------------------------------------------------------------------------
# ExecutionResult helpers
# ---------------------------------------------------------------------------

def test_execution_result_success_when_no_errors():
    r = ExecutionResult(statements_run=3)
    assert r.success is True


def test_execution_result_failure_when_errors_present():
    r = ExecutionResult(errors=["oops"])
    assert r.success is False


def test_execution_result_summary_dry_run():
    r = ExecutionResult(statements_run=2, statements_skipped=1, dry_run=True)
    assert "dry-run" in r.summary()
    assert "2 executed" in r.summary()


def test_execution_result_summary_live():
    r = ExecutionResult(statements_run=1)
    assert "dry-run" not in r.summary()


# ---------------------------------------------------------------------------
# execute_sql — no psycopg2
# ---------------------------------------------------------------------------

def test_execute_sql_no_psycopg2_returns_error():
    with patch.dict("sys.modules", {"psycopg2": None}):
        result = execute_sql("postgresql://x", ["SELECT 1"])
    assert not result.success
    assert "psycopg2" in result.errors[0]


def test_execute_sql_empty_statements_returns_empty_result():
    result = execute_sql("postgresql://x", [])
    assert result.success
    assert result.statements_run == 0


# ---------------------------------------------------------------------------
# execute_sql — mocked psycopg2
# ---------------------------------------------------------------------------

def _mock_psycopg2(side_effect=None):
    cur = MagicMock()
    if side_effect:
        cur.execute.side_effect = side_effect
    conn = MagicMock()
    conn.cursor.return_value = cur
    mod = MagicMock()
    mod.connect.return_value = conn
    return mod, conn, cur


def test_execute_sql_commits_on_success():
    mod, conn, _cur = _mock_psycopg2()
    with patch.dict("sys.modules", {"psycopg2": mod}):
        result = execute_sql("dsn", ["CREATE TABLE t (id int)"])
    assert result.success
    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()


def test_execute_sql_rollback_on_dry_run():
    mod, conn, _cur = _mock_psycopg2()
    with patch.dict("sys.modules", {"psycopg2": mod}):
        result = execute_sql("dsn", ["SELECT 1"], dry_run=True)
    assert result.success
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_execute_sql_stop_on_error():
    mod, conn, _cur = _mock_psycopg2(side_effect=Exception("syntax error"))
    with patch.dict("sys.modules", {"psycopg2": mod}):
        result = execute_sql("dsn", ["BAD SQL", "SELECT 1"])
    assert not result.success
    assert result.statements_run == 0
    assert "syntax error" in result.errors[0]


# ---------------------------------------------------------------------------
# executor_cli
# ---------------------------------------------------------------------------

def _make_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_executor_parser(sub)
    return root


def test_build_executor_parser_registers_execute():
    p = _make_parser()
    args = p.parse_args(["execute", "postgresql://localhost/db", "migration.sql"])
    assert args.cmd == "execute"
    assert args.dry_run is False


def test_run_executor_cmd_missing_file(tmp_path):
    args = SimpleNamespace(
        sql_file=str(tmp_path / "nonexistent.sql"),
        dsn="postgresql://x",
        dry_run=False,
        no_stop_on_error=False,
    )
    assert run_executor_cmd(args) == 1


def test_run_executor_cmd_empty_file(tmp_path):
    f = tmp_path / "empty.sql"
    f.write_text("   ", encoding="utf-8")
    args = SimpleNamespace(
        sql_file=str(f),
        dsn="postgresql://x",
        dry_run=False,
        no_stop_on_error=False,
    )
    assert run_executor_cmd(args) == 0


def test_run_executor_cmd_success(tmp_path):
    f = tmp_path / "mig.sql"
    f.write_text("SELECT 1;", encoding="utf-8")
    mod, _conn, _cur = _mock_psycopg2()
    args = SimpleNamespace(
        sql_file=str(f),
        dsn="postgresql://x",
        dry_run=False,
        no_stop_on_error=False,
    )
    with patch.dict("sys.modules", {"psycopg2": mod}):
        rc = run_executor_cmd(args)
    assert rc == 0
