"""Tests for pg_diff_cli.rollback_generator."""

import pytest
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff
from pg_diff_cli.schema_fetcher import TableColumn, TableSchema
from pg_diff_cli.rollback_generator import generate_rollback


def _col(name: str, dtype: str = "text", nullable: bool = True, default=None):
    return TableColumn(
        name=name, data_type=dtype, is_nullable=nullable, column_default=default
    )


def _table(*cols):
    return TableSchema(columns={c.name: c for c in cols})


def _empty_diff():
    return SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={},
    )


def test_no_changes_produces_comment():
    sql = generate_rollback(_empty_diff())
    assert "No changes" in sql


def test_rollback_added_table_drops_it():
    diff = SchemaDiff(
        added_tables={"users": _table(_col("id", "int"))},
        removed_tables={},
        modified_tables={},
    )
    sql = generate_rollback(diff)
    assert "DROP TABLE IF EXISTS users" in sql


def test_rollback_removed_table_recreates_it():
    diff = SchemaDiff(
        added_tables={},
        removed_tables={"orders": _table(_col("id", "int"), _col("total", "numeric"))},
        modified_tables={},
    )
    sql = generate_rollback(diff)
    assert "CREATE TABLE orders" in sql
    assert "id int" in sql
    assert "total numeric" in sql


def test_rollback_added_column_drops_it():
    table_diff = TableDiff(
        added_columns={"email": _col("email")},
        removed_columns={},
        modified_columns={},
        columns={},
    )
    diff = SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={"users": table_diff},
    )
    sql = generate_rollback(diff)
    assert "DROP COLUMN IF EXISTS email" in sql


def test_rollback_removed_column_adds_it_back():
    table_diff = TableDiff(
        added_columns={},
        removed_columns={"bio": _col("bio", "text")},
        modified_columns={},
        columns={},
    )
    diff = SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={"users": table_diff},
    )
    sql = generate_rollback(diff)
    assert "ADD COLUMN bio text" in sql


def test_rollback_modified_column_type():
    col_diff = ColumnDiff(
        old_type="varchar(100)",
        new_type="text",
        old_nullable=None,
        new_nullable=None,
        old_default=None,
        new_default=None,
    )
    table_diff = TableDiff(
        added_columns={},
        removed_columns={},
        modified_columns={"name": col_diff},
        columns={},
    )
    diff = SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={"users": table_diff},
    )
    sql = generate_rollback(diff)
    assert "ALTER COLUMN name TYPE varchar(100)" in sql


def test_rollback_nullable_change_restores_old_constraint():
    col_diff = ColumnDiff(
        old_type=None,
        new_type=None,
        old_nullable=True,
        new_nullable=False,
        old_default=None,
        new_default=None,
    )
    table_diff = TableDiff(
        added_columns={},
        removed_columns={},
        modified_columns={"status": col_diff},
        columns={},
    )
    diff = SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={"orders": table_diff},
    )
    sql = generate_rollback(diff)
    assert "DROP NOT NULL" in sql
