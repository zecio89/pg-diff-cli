"""Tests for pg_diff_cli.cli."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pg_diff_cli.cli import build_parser, run
from pg_diff_cli.schema_differ import SchemaDiff


SOURCE_DSN = "postgresql://user:pass@localhost/source"
TARGET_DSN = "postgresql://user:pass@localhost/target"


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_required_args():
    parser = build_parser()
    args = parser.parse_args([SOURCE_DSN, TARGET_DSN])
    assert args.source_dsn == SOURCE_DSN
    assert args.target_dsn == TARGET_DSN
    assert args.schema == "public"
    assert args.output is None
    assert args.no_header is False


def test_parser_optional_flags():
    parser = build_parser()
    args = parser.parse_args([SOURCE_DSN, TARGET_DSN, "--schema", "myschema", "--no-header", "-o", "out.sql"])
    assert args.schema == "myschema"
    assert args.no_header is True
    assert args.output == "out.sql"


# ---------------------------------------------------------------------------
# run() integration tests (fetch_schema mocked)
# ---------------------------------------------------------------------------

def _empty_diff():
    return SchemaDiff(added_tables={}, removed_tables={}, modified_tables={})


@patch("pg_diff_cli.cli.fetch_schema")
@patch("pg_diff_cli.cli.diff_schemas")
@patch("pg_diff_cli.cli.generate_migration")
def test_run_no_changes_returns_0(mock_gen, mock_diff, mock_fetch, capsys):
    mock_fetch.return_value = MagicMock()
    mock_diff.return_value = _empty_diff()
    mock_gen.return_value = "-- No changes detected."

    code = run([SOURCE_DSN, TARGET_DSN])

    assert code == 0
    captured = capsys.readouterr()
    assert "No changes" in captured.out


@patch("pg_diff_cli.cli.fetch_schema")
@patch("pg_diff_cli.cli.diff_schemas")
@patch("pg_diff_cli.cli.generate_migration")
def test_run_with_changes_returns_2(mock_gen, mock_diff, mock_fetch):
    mock_fetch.return_value = MagicMock()
    diff = SchemaDiff(added_tables={"foo": MagicMock()}, removed_tables={}, modified_tables={})
    mock_diff.return_value = diff
    mock_gen.return_value = "CREATE TABLE foo ();"

    code = run([SOURCE_DSN, TARGET_DSN])
    assert code == 2


@patch("pg_diff_cli.cli.fetch_schema", side_effect=Exception("connection refused"))
def test_run_fetch_error_returns_1(mock_fetch, capsys):
    code = run([SOURCE_DSN, TARGET_DSN])
    assert code == 1
    captured = capsys.readouterr()
    assert "connection refused" in captured.err


@patch("pg_diff_cli.cli.fetch_schema")
@patch("pg_diff_cli.cli.diff_schemas")
@patch("pg_diff_cli.cli.generate_migration")
def test_run_writes_output_file(mock_gen, mock_diff, mock_fetch, tmp_path, capsys):
    mock_fetch.return_value = MagicMock()
    mock_diff.return_value = _empty_diff()
    sql = "-- No changes detected."
    mock_gen.return_value = sql

    out_file = tmp_path / "migration.sql"
    code = run([SOURCE_DSN, TARGET_DSN, "-o", str(out_file)])

    assert code == 0
    assert out_file.read_text(encoding="utf-8") == sql
    captured = capsys.readouterr()
    assert "migration.sql" in captured.out
