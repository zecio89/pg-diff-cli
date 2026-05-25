"""Tests for pg_diff_cli.hash_cli."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock

from pg_diff_cli.hash_cli import build_hash_parser, run_hash_cmd
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.schema_hasher import hash_schema


def _col(name, dtype="text"):
    return TableColumn(name=name, data_type=dtype, is_nullable=True, default=None)


def _schema(*names):
    tables = {n: TableSchema(name=n, columns=[_col("id", "integer")]) for n in names}
    return DatabaseSchema(tables=tables)


def _make_parser():
    return build_hash_parser()


def test_build_hash_parser_registers_subcommands():
    p = _make_parser()
    args = p.parse_args(["compute", "snap.json"])
    assert args.hash_cmd == "compute"
    assert args.snapshot == "snap.json"


def test_build_hash_parser_compare_subcommand():
    p = _make_parser()
    args = p.parse_args(["compare", "a.json", "b.json"])
    assert args.hash_cmd == "compare"
    assert args.source == "a.json"
    assert args.target == "b.json"


def test_compute_prints_overall_hash(capsys):
    schema = _schema("users")
    args = _make_parser().parse_args(["compute", "snap.json"])
    with patch("pg_diff_cli.hash_cli._load", return_value=hash_schema(schema)):
        rc = run_hash_cmd(args)
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert len(out) == 64


def test_compute_json_flag_outputs_json(capsys):
    schema = _schema("users", "orders")
    args = _make_parser().parse_args(["compute", "snap.json", "--json"])
    with patch("pg_diff_cli.hash_cli._load", return_value=hash_schema(schema)):
        rc = run_hash_cmd(args)
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert "overall" in data
    assert "users" in data["tables"]
    assert "orders" in data["tables"]


def test_compare_identical_returns_0(capsys):
    schema = _schema("users")
    h = hash_schema(schema)
    args = _make_parser().parse_args(["compare", "a.json", "b.json"])
    with patch("pg_diff_cli.hash_cli._load", side_effect=[h, h]):
        rc = run_hash_cmd(args)
    assert rc == 0
    assert "identical" in capsys.readouterr().out


def test_compare_different_returns_2(capsys):
    s1 = _schema("users")
    s2 = DatabaseSchema(tables={
        "users": TableSchema(name="users", columns=[_col("id", "bigint")])
    })
    args = _make_parser().parse_args(["compare", "a.json", "b.json"])
    with patch("pg_diff_cli.hash_cli._load",
               side_effect=[hash_schema(s1), hash_schema(s2)]):
        rc = run_hash_cmd(args)
    out = capsys.readouterr().out
    assert rc == 2
    assert "users" in out
