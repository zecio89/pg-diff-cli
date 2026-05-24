"""Tests for pg_diff_cli.schema_filter."""
import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.schema_filter import (
    FilterOptions,
    apply_filter,
    filter_options_from_config,
)


def _col(name: str, data_type: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=data_type, nullable=nullable, default=None)


def _table(name: str) -> TableSchema:
    return TableSchema(name=name, columns={"id": _col("id", "integer", False)})


def _schema(*names: str) -> DatabaseSchema:
    return DatabaseSchema(tables={n: _table(n) for n in names})


def test_no_options_returns_all_tables():
    schema = _schema("users", "orders", "products")
    result = apply_filter(schema, None)
    assert set(result.tables.keys()) == {"users", "orders", "products"}


def test_include_tables_exact_match():
    schema = _schema("users", "orders", "products")
    opts = FilterOptions(include_tables=["users", "orders"])
    result = apply_filter(schema, opts)
    assert set(result.tables.keys()) == {"users", "orders"}


def test_exclude_tables_removes_matches():
    schema = _schema("users", "orders", "audit_log")
    opts = FilterOptions(exclude_tables=["audit_log"])
    result = apply_filter(schema, opts)
    assert "audit_log" not in result.tables
    assert "users" in result.tables


def test_include_tables_wildcard():
    schema = _schema("audit_log", "audit_events", "users")
    opts = FilterOptions(include_tables=["audit_*"])
    result = apply_filter(schema, opts)
    assert set(result.tables.keys()) == {"audit_log", "audit_events"}


def test_exclude_tables_wildcard():
    schema = _schema("tmp_foo", "tmp_bar", "users")
    opts = FilterOptions(exclude_tables=["tmp_*"])
    result = apply_filter(schema, opts)
    assert set(result.tables.keys()) == {"users"}


def test_include_schema_prefix_filters():
    schema = _schema("public.users", "analytics.events", "analytics.sessions")
    opts = FilterOptions(include_schemas=["analytics"])
    result = apply_filter(schema, opts)
    assert set(result.tables.keys()) == {"analytics.events", "analytics.sessions"}


def test_exclude_schema_prefix_filters():
    schema = _schema("public.users", "internal.secrets", "public.orders")
    opts = FilterOptions(exclude_schemas=["internal"])
    result = apply_filter(schema, opts)
    assert "internal.secrets" not in result.tables
    assert len(result.tables) == 2


def test_empty_schema_returns_empty():
    schema = DatabaseSchema(tables={})
    opts = FilterOptions(include_tables=["users"])
    result = apply_filter(schema, opts)
    assert result.tables == {}


def test_filter_options_from_config_defaults():
    opts = filter_options_from_config({})
    assert opts.include_tables == []
    assert opts.exclude_tables == []
    assert opts.include_schemas == []
    assert opts.exclude_schemas == []


def test_filter_options_from_config_reads_values():
    cfg = {
        "include_tables": ["users"],
        "exclude_schemas": ["internal"],
    }
    opts = filter_options_from_config(cfg)
    assert opts.include_tables == ["users"]
    assert opts.exclude_schemas == ["internal"]
    assert opts.exclude_tables == []
