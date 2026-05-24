"""Tests for pg_diff_cli.filter_cli."""
import argparse
import pytest

from pg_diff_cli.filter_cli import add_filter_arguments, filter_options_from_args


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_filter_arguments(p)
    return p


def test_add_filter_arguments_registers_flags():
    p = _make_parser()
    args = p.parse_args([])
    assert hasattr(args, "include_tables")
    assert hasattr(args, "exclude_tables")
    assert hasattr(args, "include_schemas")
    assert hasattr(args, "exclude_schemas")


def test_include_table_flag_appends():
    p = _make_parser()
    args = p.parse_args(["--include-table", "users", "--include-table", "orders"])
    assert args.include_tables == ["users", "orders"]


def test_exclude_table_flag_appends():
    p = _make_parser()
    args = p.parse_args(["--exclude-table", "audit_*"])
    assert args.exclude_tables == ["audit_*"]


def test_include_schema_flag():
    p = _make_parser()
    args = p.parse_args(["--include-schema", "public"])
    assert args.include_schemas == ["public"]


def test_exclude_schema_flag():
    p = _make_parser()
    args = p.parse_args(["--exclude-schema", "internal"])
    assert args.exclude_schemas == ["internal"]


def test_filter_options_from_args_returns_none_when_empty():
    p = _make_parser()
    args = p.parse_args([])
    result = filter_options_from_args(args)
    assert result is None


def test_filter_options_from_args_builds_correctly():
    p = _make_parser()
    args = p.parse_args(["--include-table", "users", "--exclude-schema", "internal"])
    result = filter_options_from_args(args)
    assert result is not None
    assert result.include_tables == ["users"]
    assert result.exclude_schemas == ["internal"]
    assert result.exclude_tables == []
    assert result.include_schemas == []


def test_filter_options_from_args_missing_attrs_defaults_empty():
    """Namespaces without filter attrs (e.g. sub-parsers) should not crash."""
    args = argparse.Namespace()
    result = filter_options_from_args(args)
    assert result is None
