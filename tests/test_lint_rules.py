"""Tests for pg_diff_cli.lint_rules."""

import pytest
from pg_diff_cli.schema_fetcher import TableColumn
from pg_diff_cli.schema_differ import ColumnDiff, TableDiff, SchemaDiff
from pg_diff_cli.lint_rules import lint_diff, LintWarning


def _col(name, dtype="text", nullable=True, default=None):
    return TableColumn(name=name, data_type=dtype, nullable=nullable,
                       default=default, is_primary_key=False)


def _col_diff(before, after):
    name = (after or before).name
    return ColumnDiff(
        column_name=name,
        before=before,
        after=after,
        added=before is None,
        removed=after is None,
        changed=before is not None and after is not None and before != after,
    )


def _table_diff(name, column_diffs, removed=False, added=False):
    return TableDiff(
        table_name=name,
        column_diffs=column_diffs,
        added=added,
        removed=removed,
    )


def _diff(tables):
    return SchemaDiff(table_diffs=tables)


# ---------------------------------------------------------------------------

def test_no_warnings_on_clean_diff():
    result = lint_diff(_diff([]))
    assert not result.has_warnings
    assert not result.has_errors


def test_drop_table_is_error():
    td = _table_diff("users", [], removed=True)
    result = lint_diff(_diff([td]))
    assert result.has_errors
    assert any("dropped" in w.message.lower() for w in result.warnings)


def test_drop_column_is_error():
    col = _col("email")
    cd = _col_diff(before=col, after=None)
    cd.removed = True
    td = _table_diff("users", [cd])
    result = lint_diff(_diff([td]))
    assert result.has_errors
    assert any("dropped" in w.message.lower() for w in result.warnings)


def test_new_not_null_no_default_is_warning():
    new_col = _col("age", dtype="integer", nullable=False, default=None)
    cd = _col_diff(before=None, after=new_col)
    td = _table_diff("users", [cd])
    result = lint_diff(_diff([td]))
    assert result.has_warnings
    assert not result.has_errors
    assert any("NOT NULL" in w.message for w in result.warnings)


def test_new_not_null_with_default_no_warning():
    new_col = _col("age", dtype="integer", nullable=False, default="0")
    cd = _col_diff(before=None, after=new_col)
    td = _table_diff("users", [cd])
    result = lint_diff(_diff([td]))
    assert not result.has_warnings


def test_type_change_is_warning():
    before = _col("score", dtype="integer")
    after = _col("score", dtype="bigint")
    cd = _col_diff(before=before, after=after)
    cd.changed = True
    td = _table_diff("results", [cd])
    result = lint_diff(_diff([td]))
    assert result.has_warnings
    assert any("type changed" in w.message.lower() for w in result.warnings)


def test_lint_warning_str_format():
    w = LintWarning(level="error", table="orders", column="total",
                    message="Column is being dropped")
    assert str(w) == "[ERROR] orders.total: Column is being dropped"


def test_lint_warning_str_no_column():
    w = LintWarning(level="error", table="orders", column=None,
                    message="Table is being dropped")
    assert str(w) == "[ERROR] orders: Table is being dropped"
