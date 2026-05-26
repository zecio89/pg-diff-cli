"""Tests for pg_diff_cli.export_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pg_diff_cli.export_cli import build_export_parser, run_export_cmd
from pg_diff_cli.schema_fetcher import TableColumn, TableSchema, DatabaseSchema


def _make_parser() -> argparse.ArgumentParser:
    return build_export_parser()


def _col(name: str) -> TableColumn:
    return TableColumn(name=name, data_type="text", nullable=True, default=None)


def _schema() -> DatabaseSchema:
    return DatabaseSchema(tables={"t": TableSchema(columns=[_col("id")])})


def test_build_export_parser_returns_parser():
    parser = _make_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_export_parser_snapshot_positional():
    parser = _make_parser()
    args = parser.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"


def test_export_parser_default_format_is_json():
    parser = _make_parser()
    args = parser.parse_args(["snap.json"])
    assert args.fmt == "json"


def test_export_parser_format_csv():
    parser = _make_parser()
    args = parser.parse_args(["snap.json", "--format", "csv"])
    assert args.fmt == "csv"


def test_run_export_missing_file_returns_1(tmp_path):
    args = argparse.Namespace(
        snapshot=str(tmp_path / "missing.json"),
        fmt="json",
        output=None,
        indent=2,
    )
    assert run_export_cmd(args) == 1


def test_run_export_invalid_snapshot_returns_1(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json")
    args = argparse.Namespace(
        snapshot=str(bad), fmt="json", output=None, indent=2
    )
    with patch("pg_diff_cli.export_cli.load_snapshot", return_value=None):
        assert run_export_cmd(args) == 1


def test_run_export_stdout_returns_0(tmp_path, capsys):
    snap = tmp_path / "snap.json"
    snap.write_text("{}")
    args = argparse.Namespace(
        snapshot=str(snap), fmt="json", output=None, indent=2
    )
    with patch("pg_diff_cli.export_cli.load_snapshot", return_value=_schema()):
        rc = run_export_cmd(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "tables" in data


def test_run_export_to_file(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text("{}")
    out = tmp_path / "out" / "schema.json"
    args = argparse.Namespace(
        snapshot=str(snap), fmt="json", output=str(out), indent=2
    )
    with patch("pg_diff_cli.export_cli.load_snapshot", return_value=_schema()):
        rc = run_export_cmd(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "tables" in data
