"""Tests for pg_diff_cli.schema_diff_summary."""
import pytest

from pg_diff_cli.schema_differ import ColumnDiff, SchemaDiff, TableDiff
from pg_diff_cli.schema_fetcher import TableColumn
from pg_diff_cli.schema_diff_summary import DiffSummary, TableSummary, summarize_diff


def _col(name="id", dtype="integer", nullable=False):
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=None)


def _table_diff(name, added=False, removed=False, col_diffs=None):
    return TableDiff(
        table_name=name,
        added=added,
        removed=removed,
        column_diffs=col_diffs or [],
    )


def _col_diff(name, added=False, removed=False, old=None, new=None):
    col = _col(name)
    return ColumnDiff(
        column_name=name,
        added=added,
        removed=removed,
        old=old or col,
        new=new or col,
    )


def test_empty_diff_is_empty():
    diff = SchemaDiff(table_diffs=[])
    summary = summarize_diff(diff)
    assert summary.is_empty
    assert summary.total_changes == 0


def test_added_table_counted():
    diff = SchemaDiff(table_diffs=[_table_diff("users", added=True)])
    summary = summarize_diff(diff)
    assert summary.tables_added == 1
    assert summary.tables_removed == 0
    assert not summary.is_empty


def test_removed_table_counted():
    diff = SchemaDiff(table_diffs=[_table_diff("old_table", removed=True)])
    summary = summarize_diff(diff)
    assert summary.tables_removed == 1


def test_modified_table_counted():
    cd = _col_diff("email", added=True)
    diff = SchemaDiff(table_diffs=[_table_diff("users", col_diffs=[cd])])
    summary = summarize_diff(diff)
    assert summary.tables_modified == 1
    assert summary.columns_added == 1


def test_column_removed_counted():
    cd = _col_diff("old_col", removed=True)
    diff = SchemaDiff(table_diffs=[_table_diff("t", col_diffs=[cd])])
    summary = summarize_diff(diff)
    assert summary.columns_removed == 1


def test_column_modified_counted():
    old = _col("x", dtype="integer")
    new = _col("x", dtype="bigint")
    cd = ColumnDiff(column_name="x", added=False, removed=False, old=old, new=new)
    diff = SchemaDiff(table_diffs=[_table_diff("t", col_diffs=[cd])])
    summary = summarize_diff(diff)
    assert summary.columns_modified == 1


def test_as_text_no_changes():
    summary = DiffSummary()
    assert summary.as_text() == "No schema differences found."


def test_as_text_with_changes():
    summary = DiffSummary(tables_added=1, columns_removed=2)
    text = summary.as_text()
    assert "Tables added:    1" in text
    assert "Columns removed: 2" in text


def test_table_summary_has_changes_false_when_clean():
    ts = TableSummary(name="t")
    assert not ts.has_changes


def test_table_details_populated():
    cd = _col_diff("col", added=True)
    diff = SchemaDiff(table_diffs=[_table_diff("users", col_diffs=[cd])])
    summary = summarize_diff(diff)
    assert len(summary.table_details) == 1
    assert summary.table_details[0].name == "users"
    assert summary.table_details[0].columns_added == 1
