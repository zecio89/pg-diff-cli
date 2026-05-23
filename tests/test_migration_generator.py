"""Tests for migration_generator module."""

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.schema_differ import diff_schemas
from pg_diff_cli.migration_generator import generate_migration


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(column_name=name, data_type=dtype, is_nullable=nullable)


def _table(name: str, cols: list) -> TableSchema:
    return TableSchema(table_name=name, columns=cols)


def test_no_changes_produces_comment():
    schema = DatabaseSchema(tables=[_table("users", [_col("id", "integer")])])
    diff = diff_schemas(schema, schema)
    sql = generate_migration(diff)
    assert "No changes" in sql


def test_drop_table_sql():
    source = DatabaseSchema(tables=[_table("old_table", [_col("id")])])
    target = DatabaseSchema(tables=[])
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "DROP TABLE IF EXISTS old_table;" in sql


def test_add_column_sql():
    source = DatabaseSchema(tables=[_table("users", [_col("id", "integer")])])
    target = DatabaseSchema(tables=[_table("users", [_col("id", "integer"), _col("email", "text")])])
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "ALTER TABLE users ADD COLUMN email text;" in sql


def test_add_not_null_column_sql():
    source = DatabaseSchema(tables=[_table("users", [_col("id", "integer")])])
    target = DatabaseSchema(
        tables=[_table("users", [_col("id", "integer"), _col("username", "text", nullable=False)])]
    )
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "ADD COLUMN username text NOT NULL" in sql


def test_drop_column_sql():
    source = DatabaseSchema(tables=[_table("users", [_col("id"), _col("legacy")])])
    target = DatabaseSchema(tables=[_table("users", [_col("id")])])
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "ALTER TABLE users DROP COLUMN legacy;" in sql


def test_alter_column_type_sql():
    source = DatabaseSchema(tables=[_table("users", [_col("score", "integer")])])
    target = DatabaseSchema(tables=[_table("users", [_col("score", "bigint")])])
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "ALTER TABLE users ALTER COLUMN score TYPE bigint;" in sql


def test_set_not_null_sql():
    source = DatabaseSchema(tables=[_table("users", [_col("name", "text", nullable=True)])])
    target = DatabaseSchema(tables=[_table("users", [_col("name", "text", nullable=False)])])
    diff = diff_schemas(source, target)
    sql = generate_migration(diff)
    assert "SET NOT NULL" in sql
