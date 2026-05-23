"""Tests for pg_diff_cli.baseline_cli."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pg_diff_cli.baseline_cli import build_baseline_parser, run_baseline_cmd
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.schema_differ import SchemaDiff


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables={}, removed_tables={}, changed_tables={})


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        baseline_cmd="diff",
        name="v1",
        dsn="postgresql://localhost/test",
        schema="public",
        directory="/tmp/baselines",
        sql=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_baseline_parser_registers_subcommands() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_baseline_parser(sub)
    args = parser.parse_args(["baseline", "list", "--dir", "/tmp"])
    assert args.baseline_cmd == "list"


def test_run_save_returns_0(tmp_path: Path) -> None:
    schema = DatabaseSchema(tables={})
    with patch("pg_diff_cli.baseline_cli.fetch_schema", return_value=schema):
        args = _make_args(baseline_cmd="save", name="v1", directory=str(tmp_path))
        code = run_baseline_cmd(args)
    assert code == 0
    assert (tmp_path / "v1.json").exists()


def test_run_list_empty(tmp_path: Path, capsys) -> None:
    args = _make_args(baseline_cmd="list", directory=str(tmp_path))
    code = run_baseline_cmd(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "No baselines" in captured.out


def test_run_diff_no_changes_returns_0(tmp_path: Path) -> None:
    diff = _empty_diff()
    with patch("pg_diff_cli.baseline_cli.fetch_schema", return_value=DatabaseSchema(tables={})), \
         patch("pg_diff_cli.baseline_cli.diff_against_baseline", return_value=diff):
        args = _make_args(baseline_cmd="diff", directory=str(tmp_path))
        code = run_baseline_cmd(args)
    assert code == 0


def test_run_diff_with_changes_returns_2(tmp_path: Path) -> None:
    from pg_diff_cli.schema_fetcher import TableSchema
    added = {"new_table": TableSchema(name="new_table", columns=[])}
    diff = SchemaDiff(added_tables=added, removed_tables={}, changed_tables={})
    with patch("pg_diff_cli.baseline_cli.fetch_schema", return_value=DatabaseSchema(tables={})), \
         patch("pg_diff_cli.baseline_cli.diff_against_baseline", return_value=diff):
        args = _make_args(baseline_cmd="diff", directory=str(tmp_path))
        code = run_baseline_cmd(args)
    assert code == 2


def test_run_diff_sql_flag_prints_sql(tmp_path: Path, capsys) -> None:
    diff = _empty_diff()
    with patch("pg_diff_cli.baseline_cli.fetch_schema", return_value=DatabaseSchema(tables={})), \
         patch("pg_diff_cli.baseline_cli.diff_against_baseline", return_value=diff):
        args = _make_args(baseline_cmd="diff", sql=True, directory=str(tmp_path))
        run_baseline_cmd(args)
    captured = capsys.readouterr()
    assert captured.out  # some SQL / comment was printed
