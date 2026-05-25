"""Tests for pg_diff_cli.statement_tagger."""
import pytest

from pg_diff_cli.statement_tagger import (
    RiskLevel,
    TaggedStatement,
    filter_by_risk,
    tag_statements,
)


def test_empty_input_returns_empty_list():
    assert tag_statements([]) == []


def test_whitespace_only_statements_are_skipped():
    result = tag_statements(["   ", "\n"])
    assert result == []


def test_create_table_is_low_risk():
    result = tag_statements(["CREATE TABLE foo (id INT)"])
    assert len(result) == 1
    assert result[0].risk == RiskLevel.LOW


def test_drop_table_is_high_risk():
    result = tag_statements(["DROP TABLE foo"])
    assert result[0].risk == RiskLevel.HIGH


def test_drop_column_is_high_risk():
    result = tag_statements(["ALTER TABLE foo DROP COLUMN bar"])
    assert result[0].risk == RiskLevel.HIGH


def test_alter_table_add_column_is_medium_risk():
    result = tag_statements(["ALTER TABLE foo ADD COLUMN bar TEXT"])
    assert result[0].risk == RiskLevel.MEDIUM


def test_destructive_tag_on_drop():
    result = tag_statements(["DROP TABLE foo"])
    assert "destructive" in result[0].tags


def test_additive_tag_on_create():
    result = tag_statements(["CREATE TABLE foo (id INT)"])
    assert "additive" in result[0].tags


def test_constraint_tag_on_not_null():
    result = tag_statements(["ALTER TABLE foo ALTER COLUMN bar SET NOT NULL"])
    assert "constraint" in result[0].tags


def test_default_tag_on_set_default():
    result = tag_statements(["ALTER TABLE foo ALTER COLUMN bar SET DEFAULT 0"])
    assert "default" in result[0].tags


def test_filter_by_risk_high_only():
    stmts = [
        "CREATE TABLE foo (id INT)",
        "ALTER TABLE foo ADD COLUMN bar TEXT",
        "DROP TABLE foo",
    ]
    tagged = tag_statements(stmts)
    high_only = filter_by_risk(tagged, RiskLevel.HIGH)
    assert len(high_only) == 1
    assert high_only[0].risk == RiskLevel.HIGH


def test_filter_by_risk_medium_includes_high():
    stmts = [
        "CREATE TABLE foo (id INT)",
        "ALTER TABLE foo ADD COLUMN bar TEXT",
        "DROP TABLE foo",
    ]
    tagged = tag_statements(stmts)
    result = filter_by_risk(tagged, RiskLevel.MEDIUM)
    risks = {t.risk for t in result}
    assert RiskLevel.LOW not in risks
    assert RiskLevel.MEDIUM in risks
    assert RiskLevel.HIGH in risks


def test_tagged_statement_str_contains_risk_label():
    ts = TaggedStatement(sql="DROP TABLE foo", risk=RiskLevel.HIGH, tags=["destructive"])
    s = str(ts)
    assert "HIGH" in s
    assert "destructive" in s
