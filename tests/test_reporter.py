"""Tests for pg_diff_cli.reporter."""

from __future__ import annotations

import pytest

from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff
from pg_diff_cli.reporter import ReportOptions, format_report


def _col(name: str, **kwargs) -> ColumnDiff:
    defaults = dict(
        column_name=name,
        old_type="text",
        new_type="text",
        old_nullable=True,
        new_nullable=True,
        added=False,
        removed=False,
        type_changed=False,
        nullable_changed=False,
    )
    defaults.update(kwargs)
    return ColumnDiff(**defaults)


def _table(name: str, cols: list[ColumnDiff] | None = None, **kwargs) -> TableDiff:
    defaults = dict(table_name=name, added=False, removed=False, column_diffs=cols or [])
    defaults.update(kwargs)
    return TableDiff(**defaults)


OPTS_NO_COLOR = ReportOptions(color=False)


def test_no_diff_message():
    diff = SchemaDiff(table_diffs=[])
    report = format_report(diff, OPTS_NO_COLOR)
    assert "No schema differences found" in report


def test_added_table_shown_with_plus():
    diff = SchemaDiff(table_diffs=[_table("users", added=True)])
    report = format_report(diff, OPTS_NO_COLOR)
    assert "+ table users" in report


def test_removed_table_shown_with_minus():
    diff = SchemaDiff(table_diffs=[_table("orders", removed=True)])
    report = format_report(diff, OPTS_NO_COLOR)
    assert "- table orders" in report


def test_modified_table_shown_with_tilde():
    col = _col("email", type_changed=True, old_type="varchar", new_type="text")
    diff = SchemaDiff(table_diffs=[_table("users", cols=[col])])
    report = format_report(diff, OPTS_NO_COLOR)
    assert "~ table users" in report
    assert "~ column email" in report
    assert "varchar -> text" in report


def test_added_column_in_verbose_mode():
    col = _col("bio", added=True, new_type="text")
    diff = SchemaDiff(table_diffs=[_table("users", added=True, cols=[col])])
    opts = ReportOptions(color=False, verbose=True)
    report = format_report(diff, opts)
    assert "+ column bio" in report


def test_nullable_change_reported():
    col = _col("age", nullable_changed=True, old_nullable=True, new_nullable=False)
    diff = SchemaDiff(table_diffs=[_table("users", cols=[col])])
    report = format_report(diff, OPTS_NO_COLOR)
    assert "nullable True -> False" in report


def test_table_count_in_summary():
    diff = SchemaDiff(
        table_diffs=[
            _table("a", added=True),
            _table("b", removed=True),
        ]
    )
    report = format_report(diff, OPTS_NO_COLOR)
    assert "2 table(s) with differences" in report


def test_color_codes_present_when_enabled():
    diff = SchemaDiff(table_diffs=[_table("users", added=True)])
    opts = ReportOptions(color=True)
    report = format_report(diff, opts)
    assert "\033[" in report
