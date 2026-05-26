"""Tests for pg_diff_cli.summary_cli."""
import argparse
import io
import json

import pytest

from pg_diff_cli.schema_differ import ColumnDiff, SchemaDiff, TableDiff
from pg_diff_cli.schema_fetcher import TableColumn
from pg_diff_cli.summary_cli import build_summary_parser, run_summary_cmd


def _col(name="id", dtype="integer"):
    return TableColumn(name=name, data_type=dtype, is_nullable=False, default=None)


def _empty_diff():
    return SchemaDiff(table_diffs=[])


def _added_table_diff():
    return SchemaDiff(
        table_diffs=[
            TableDiff(table_name="orders", added=True, removed=False, column_diffs=[])
        ]
    )


def _make_args(**kwargs):
    defaults = {"format": "text", "show_tables": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_summary_parser_returns_parser():
    parser = build_summary_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_summary_parser_format_choices():
    parser = build_summary_parser()
    args = parser.parse_args(["--format", "json"])
    assert args.format == "json"


def test_build_summary_parser_show_tables_flag():
    parser = build_summary_parser()
    args = parser.parse_args(["--show-tables"])
    assert args.show_tables is True


def test_run_summary_empty_diff_returns_0():
    out = io.StringIO()
    code = run_summary_cmd(_empty_diff(), _make_args(), out=out)
    assert code == 0


def test_run_summary_empty_diff_text_message():
    out = io.StringIO()
    run_summary_cmd(_empty_diff(), _make_args(), out=out)
    assert "No schema differences found" in out.getvalue()


def test_run_summary_with_changes_returns_2():
    out = io.StringIO()
    code = run_summary_cmd(_added_table_diff(), _make_args(), out=out)
    assert code == 2


def test_run_summary_text_shows_counts():
    out = io.StringIO()
    run_summary_cmd(_added_table_diff(), _make_args(), out=out)
    text = out.getvalue()
    assert "Tables added:    1" in text


def test_run_summary_json_format():
    out = io.StringIO()
    run_summary_cmd(_added_table_diff(), _make_args(format="json"), out=out)
    data = json.loads(out.getvalue())
    assert data["tables_added"] == 1
    assert data["total_changes"] == 1


def test_run_summary_json_includes_tables_when_flag_set():
    out = io.StringIO()
    run_summary_cmd(
        _added_table_diff(), _make_args(format="json", show_tables=True), out=out
    )
    data = json.loads(out.getvalue())
    assert "tables" in data
    assert data["tables"][0]["name"] == "orders"


def test_run_summary_show_tables_text_lists_table():
    out = io.StringIO()
    run_summary_cmd(_added_table_diff(), _make_args(show_tables=True), out=out)
    assert "orders" in out.getvalue()
    assert "[+]" in out.getvalue()
