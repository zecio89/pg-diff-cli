"""Tests for pg_diff_cli.cache_cli."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from pg_diff_cli.cache_cli import build_cache_parser, run_cache_cmd
from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_parser() -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:  # type: ignore[type-arg]
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_cache_parser(sub)
    return parser, sub


def _col() -> TableColumn:
    return TableColumn(name="id", data_type="integer", is_nullable=False, default=None)


def _schema() -> DatabaseSchema:
    t = TableSchema(name="users", columns=[_col()])
    return DatabaseSchema(tables={"users": t})


# ---------------------------------------------------------------------------
# parser tests
# ---------------------------------------------------------------------------

def test_build_cache_parser_registers_subcommands() -> None:
    parser, _ = _make_parser()
    args = parser.parse_args(["cache", "clear"])
    assert args.cache_cmd == "clear"


def test_status_subcommand_parses_dsn() -> None:
    parser, _ = _make_parser()
    args = parser.parse_args(["cache", "status", "--dsn", "postgresql://localhost/db"])
    assert args.dsn == "postgresql://localhost/db"
    assert args.schema == "public"


def test_invalidate_requires_dsn() -> None:
    parser, _ = _make_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["cache", "invalidate"])


# ---------------------------------------------------------------------------
# run_cache_cmd tests
# ---------------------------------------------------------------------------

def test_run_clear_returns_0(tmp_path: Path) -> None:
    args = argparse.Namespace(cache_cmd="clear")
    assert run_cache_cmd(args, cache_dir=tmp_path) == 0


def test_run_invalidate_missing_returns_0(tmp_path: Path) -> None:
    args = argparse.Namespace(cache_cmd="invalidate", dsn="dsn://x", schema="public")
    assert run_cache_cmd(args, cache_dir=tmp_path) == 0


def test_run_status_miss_returns_1(tmp_path: Path) -> None:
    args = argparse.Namespace(
        cache_cmd="status", dsn="dsn://x", schema="public", ttl=300
    )
    assert run_cache_cmd(args, cache_dir=tmp_path) == 1


def test_run_status_hit_returns_0(tmp_path: Path) -> None:
    from pg_diff_cli.cache import save_cached_schema

    save_cached_schema("dsn://x", "public", _schema(), cache_dir=tmp_path)
    args = argparse.Namespace(
        cache_cmd="status", dsn="dsn://x", schema="public", ttl=300
    )
    assert run_cache_cmd(args, cache_dir=tmp_path) == 0


def test_run_unknown_cmd_returns_2(tmp_path: Path) -> None:
    args = argparse.Namespace(cache_cmd="bogus")
    assert run_cache_cmd(args, cache_dir=tmp_path) == 2
