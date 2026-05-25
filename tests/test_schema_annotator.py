"""Tests for pg_diff_cli.schema_annotator."""
from __future__ import annotations

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff
from pg_diff_cli.schema_annotator import (
    AnnotatedSchema,
    TableAnnotation,
    annotate_diff,
    _find_table_diff,
)


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=None)


def _table(name: str, *cols: TableColumn) -> TableSchema:
    return TableSchema(name=name, columns={c.name: c for c in cols})


def _empty_schema() -> DatabaseSchema:
    return DatabaseSchema(tables={})


def _annotated() -> AnnotatedSchema:
    return AnnotatedSchema(schema=_empty_schema())


# --- AnnotatedSchema unit tests ---

def test_annotate_table_stores_note():
    ann = _annotated()
    ann.annotate_table("users", "Core user table")
    assert ann.get_table_note("users") == "Core user table"


def test_annotate_column_stores_note():
    ann = _annotated()
    ann.annotate_column("users", "email", "Must be unique")
    assert ann.get_column_note("users", "email") == "Must be unique"


def test_get_table_note_missing_returns_none():
    ann = _annotated()
    assert ann.get_table_note("nonexistent") is None


def test_get_column_note_missing_table_returns_none():
    ann = _annotated()
    assert ann.get_column_note("nonexistent", "col") is None


def test_get_column_note_missing_column_returns_none():
    ann = _annotated()
    ann.annotate_table("users", "some note")
    assert ann.get_column_note("users", "missing_col") is None


def test_annotate_table_twice_overwrites():
    ann = _annotated()
    ann.annotate_table("users", "first")
    ann.annotate_table("users", "second")
    assert ann.get_table_note("users") == "second"


# --- annotate_diff tests ---

def _make_diff(added=(), removed=(), modified=()) -> SchemaDiff:
    return SchemaDiff(
        added_tables=list(added),
        removed_tables=list(removed),
        modified_tables=list(modified),
    )


def _table_diff(name: str) -> TableDiff:
    return TableDiff(
        table_name=name,
        added_columns=[],
        removed_columns=[],
        modified_columns=[],
    )


def test_annotate_diff_no_annotations_returns_empty():
    ann = _annotated()
    diff = _make_diff(added=[_table_diff("orders")])
    assert annotate_diff(diff, ann) == []


def test_annotate_diff_table_note_appears():
    ann = _annotated()
    ann.annotate_table("orders", "Main orders table")
    diff = _make_diff(added=[_table_diff("orders")])
    lines = annotate_diff(diff, ann)
    assert any("Main orders table" in l for l in lines)


def test_annotate_diff_column_note_appears():
    ann = _annotated()
    ann.annotate_column("orders", "total", "Always in cents")
    col_diff = ColumnDiff(column_name="total", old_type=None, new_type="integer",
                         old_nullable=None, new_nullable=False)
    td = TableDiff(table_name="orders", added_columns=[col_diff],
                   removed_columns=[], modified_columns=[])
    diff = _make_diff(modified=[td])
    lines = annotate_diff(diff, ann)
    assert any("Always in cents" in l for l in lines)


def test_find_table_diff_returns_correct_entry():
    td = _table_diff("products")
    diff = _make_diff(added=[td])
    result = _find_table_diff(diff, "products")
    assert result is td


def test_find_table_diff_missing_returns_none():
    diff = _make_diff()
    assert _find_table_diff(diff, "ghost") is None
