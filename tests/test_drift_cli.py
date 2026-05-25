"""Unit tests for pg_diff_cli.drift_cli."""
from __future__ import annotations

import argparse
import os
import tempfile
from unittest.mock import MagicMock, patch

from pg_diff_cli.drift_cli import build_drift_parser, run_drift_cmd
from pg_diff_cli.drift_detector import DriftResult
from pg_diff_cli.schema_differ import SchemaDiff
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.snapshot import save_snapshot


def _col(name: str) -> TableColumn:
    return TableColumn(name=name, data_type="text", is_nullable=True, default=None)


def _schema(*names: str) -> DatabaseSchema:
    tables = {n: TableSchema(name=n, columns=[_col("id")]) for n in names}
    return DatabaseSchema(tables=tables)


def _make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_drift_parser(sub)
    return root


def test_build_drift_parser_registers_subcommand():
    parser = _make_parser()
    args = parser.parse_args(["drift", "postgres://localhost/db", "snap.json"])
    assert args.command == "drift"
    assert args.dsn == "postgres://localhost/db"
    assert args.snapshot == "snap.json"


def test_build_drift_parser_defaults():
    parser = _make_parser()
    args = parser.parse_args(["drift", "dsn", "snap.json"])
    assert args.schema == "public"
    assert args.baseline_name == "snapshot"
    assert not args.no_color
    assert not args.exit_code


def test_run_drift_cmd_no_drift_returns_0():
    s = _schema("users")
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    save_snapshot(s, tmp.name)
    try:
        args = argparse.Namespace(
            dsn="postgres://localhost/db",
            snapshot=tmp.name,
            baseline_name="v1",
            schema="public",
            no_color=True,
            exit_code=True,
        )
        with patch("pg_diff_cli.drift_cli.fetch_schema", return_value=s):
            code = run_drift_cmd(args)
        assert code == 0
    finally:
        os.unlink(tmp.name)


def test_run_drift_cmd_drift_with_exit_code_returns_2():
    baseline = _schema("users")
    live = _schema("users", "orders")
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    save_snapshot(baseline, tmp.name)
    try:
        args = argparse.Namespace(
            dsn="postgres://localhost/db",
            snapshot=tmp.name,
            baseline_name="v1",
            schema="public",
            no_color=True,
            exit_code=True,
        )
        with patch("pg_diff_cli.drift_cli.fetch_schema", return_value=live):
            code = run_drift_cmd(args)
        assert code == 2
    finally:
        os.unlink(tmp.name)


def test_run_drift_cmd_missing_snapshot_returns_1():
    args = argparse.Namespace(
        dsn="postgres://localhost/db",
        snapshot="/no/such/file.json",
        baseline_name="v1",
        schema="public",
        no_color=True,
        exit_code=False,
    )
    with patch("pg_diff_cli.drift_cli.fetch_schema", return_value=_schema("users")):
        code = run_drift_cmd(args)
    assert code == 1
