"""Tests for schema_differ module."""

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.schema_differ import diff_schemas


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(column_name=name, data_type=dtype, is_nullable=nullable)


def _table(name: str, cols: list) -> TableSchema:
    return TableSchema(table_name=name, columns=cols)


def test_diff_no_changes():
    schema = DatabaseSchema(tables=[_table("users", [_col("id", "integer")])])
    result = diff_schemas(schema, schema)
    assert result.is_empty


def test_diff_added_table():
    source = DatabaseSchema(tables=[])
    target = DatabaseSchema(tables=[_table("orders", [_col("id", "integer")])])
    result = diff_schemas(source, target)
    assert len(result.table_diffs) == 1
    assert result.table_diffs[0].kind == "added"
    assert result.table_diffs[0].table == "orders"


def test_diff_removed_table():
    source = DatabaseSchema(tables=[_table("orders", [_col("id", "integer")])])
    target = DatabaseSchema(tables=[])
    result = diff_schemas(source, target)
    assert len(result.table_diffs) == 1
    assert result.table_diffs[0].kind == "removed"


def test_diff_added_column():
    source = DatabaseSchema(tables=[_table("users", [_col("id", "integer")])])
    target = DatabaseSchema(tables=[_table("users", [_col("id", "integer"), _col("email", "text")])])
    result = diff_schemas(source, target)
    assert len(result.table_diffs) == 1
    td = result.table_diffs[0]
    assert td.kind == "modified"
    assert len(td.column_diffs) == 1
    assert td.column_diffs[0].kind == "added"
    assert td.column_diffs[0].column == "email"


def test_diff_modified_column_type():
    source = DatabaseSchema(tables=[_table("users", [_col("age", "integer")])])
    target = DatabaseSchema(tables=[_table("users", [_col("age", "bigint")])])
    result = diff_schemas(source, target)
    td = result.table_diffs[0]
    assert td.column_diffs[0].kind == "modified"
    assert td.column_diffs[0].old_column.data_type == "integer"
    assert td.column_diffs[0].new_column.data_type == "bigint"


def test_diff_modified_nullable():
    source = DatabaseSchema(tables=[_table("users", [_col("name", "text", nullable=True)])])
    target = DatabaseSchema(tables=[_table("users", [_col("name", "text", nullable=False)])])
    result = diff_schemas(source, target)
    cd = result.table_diffs[0].column_diffs[0]
    assert cd.kind == "modified"
