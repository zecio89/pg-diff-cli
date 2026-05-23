"""Tests for pg_diff_cli.ignore_rules."""

from pg_diff_cli.schema_fetcher import TableColumn, TableSchema
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff
from pg_diff_cli.ignore_rules import IgnoreRules, apply_ignore_rules, ignore_rules_from_config


def _col(name: str, data_type: str = "text") -> ColumnDiff:
    return ColumnDiff(column_name=name, old_type=data_type, new_type=data_type)


def _table_diff(name: str, added=(), removed=(), changed=()) -> TableDiff:
    return TableDiff(
        table_name=name,
        added_columns=list(added),
        removed_columns=list(removed),
        changed_columns=list(changed),
    )


def _schema_table(name: str) -> TableSchema:
    return TableSchema(table_name=name, columns=[])


def _diff(**kwargs) -> SchemaDiff:
    return SchemaDiff(
        added_tables=kwargs.get("added_tables", []),
        removed_tables=kwargs.get("removed_tables", []),
        changed_tables=kwargs.get("changed_tables", []),
    )


def test_no_rules_returns_diff_unchanged():
    original = _diff(
        added_tables=[_schema_table("users")],
        changed_tables=[_table_diff("orders", added=[_col("note")])],
    )
    result = apply_ignore_rules(original, IgnoreRules())
    assert len(result.added_tables) == 1
    assert len(result.changed_tables) == 1


def test_ignore_table_by_exact_name():
    diff = _diff(added_tables=[_schema_table("audit_log"), _schema_table("users")])
    rules = IgnoreRules(tables=["audit_log"])
    result = apply_ignore_rules(diff, rules)
    assert len(result.added_tables) == 1
    assert result.added_tables[0].table_name == "users"


def test_ignore_table_by_glob_pattern():
    diff = _diff(
        removed_tables=[
            _schema_table("tmp_foo"),
            _schema_table("tmp_bar"),
            _schema_table("orders"),
        ]
    )
    rules = IgnoreRules(tables=["tmp_*"])
    result = apply_ignore_rules(diff, rules)
    assert len(result.removed_tables) == 1
    assert result.removed_tables[0].table_name == "orders"


def test_ignore_column_removes_column_diff():
    diff = _diff(
        changed_tables=[
            _table_diff("users", added=[_col("email"), _col("updated_at")])
        ]
    )
    rules = IgnoreRules(columns=["users.updated_at"])
    result = apply_ignore_rules(diff, rules)
    assert len(result.changed_tables) == 1
    assert len(result.changed_tables[0].added_columns) == 1
    assert result.changed_tables[0].added_columns[0].column_name == "email"


def test_ignore_column_glob():
    diff = _diff(
        changed_tables=[
            _table_diff("events", removed=[_col("tmp_col1"), _col("tmp_col2"), _col("id")])
        ]
    )
    rules = IgnoreRules(columns=["events.tmp_*"])
    result = apply_ignore_rules(diff, rules)
    remaining = result.changed_tables[0].removed_columns
    assert len(remaining) == 1
    assert remaining[0].column_name == "id"


def test_table_diff_removed_entirely_when_all_columns_ignored():
    diff = _diff(
        changed_tables=[
            _table_diff("users", added=[_col("updated_at")])
        ]
    )
    rules = IgnoreRules(columns=["users.updated_at"])
    result = apply_ignore_rules(diff, rules)
    assert result.changed_tables == []


def test_ignore_rules_from_config():
    cfg = {"tables": ["audit_*"], "columns": ["*.created_at"]}
    rules = ignore_rules_from_config(cfg)
    assert rules.tables == ["audit_*"]
    assert rules.columns == ["*.created_at"]


def test_ignore_rules_from_config_defaults_to_empty():
    rules = ignore_rules_from_config({})
    assert rules.tables == []
    assert rules.columns == []
