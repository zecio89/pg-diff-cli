"""Tests for pg_diff_cli.sql_normalizer."""

from __future__ import annotations

import pytest

from pg_diff_cli.sql_normalizer import (
    NormalizeOptions,
    NormalizeResult,
    normalize_sql,
    normalize_statements,
)


def test_normalize_sql_returns_normalize_result():
    result = normalize_sql("select 1")
    assert isinstance(result, NormalizeResult)


def test_uppercase_keywords_default():
    result = normalize_sql("alter table foo add column bar text")
    assert "ALTER" in result.normalized
    assert "TABLE" in result.normalized
    assert "ADD" in result.normalized
    assert "COLUMN" in result.normalized


def test_uppercase_keywords_disabled():
    options = NormalizeOptions(uppercase_keywords=False)
    result = normalize_sql("alter table foo", options)
    assert "alter" in result.normalized
    assert "ALTER" not in result.normalized


def test_collapse_whitespace():
    result = normalize_sql("CREATE   TABLE   foo  (id  int)")
    assert "  " not in result.normalized


def test_collapse_whitespace_disabled():
    options = NormalizeOptions(collapse_whitespace=False)
    result = normalize_sql("CREATE   TABLE foo", options)
    assert "   " in result.normalized


def test_strip_trailing_whitespace():
    result = normalize_sql("CREATE TABLE foo   \nADD COLUMN bar text   ")
    for line in result.normalized.splitlines():
        assert line == line.rstrip()


def test_remove_inline_comments():
    options = NormalizeOptions(remove_inline_comments=True)
    result = normalize_sql("CREATE TABLE foo -- this is a table", options)
    assert "--" not in result.normalized
    assert "this is a table" not in result.normalized


def test_remove_inline_comments_disabled_by_default():
    result = normalize_sql("CREATE TABLE foo -- keep this")
    assert "-- keep this" in result.normalized


def test_was_changed_true_when_modified():
    result = normalize_sql("create table foo")
    assert result.was_changed is True


def test_was_changed_false_when_identical():
    options = NormalizeOptions(
        uppercase_keywords=False,
        collapse_whitespace=False,
        strip_trailing_whitespace=False,
        remove_inline_comments=False,
    )
    sql = "CREATE TABLE foo"
    result = normalize_sql(sql, options)
    assert result.was_changed is False


def test_changes_list_populated():
    result = normalize_sql("create   table foo ")
    assert len(result.changes) > 0


def test_normalize_statements_processes_all():
    stmts = ["create table a", "drop table b"]
    results = normalize_statements(stmts)
    assert len(results) == 2
    assert all(isinstance(r, NormalizeResult) for r in results)


def test_normalize_statements_empty_list():
    results = normalize_statements([])
    assert results == []


def test_original_preserved_in_result():
    original = "create table foo"
    result = normalize_sql(original)
    assert result.original == original
