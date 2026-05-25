"""Tests for pg_diff_cli.tag_integration."""
from pg_diff_cli.schema_differ import ColumnDiff, SchemaDiff, TableDiff
from pg_diff_cli.schema_fetcher import TableColumn
from pg_diff_cli.statement_tagger import RiskLevel
from pg_diff_cli.tag_integration import TaggedMigration, risk_gate, tag_migration_from_diff


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=nullable, default=None)


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables={}, removed_tables={}, modified_tables={})


def test_empty_diff_produces_empty_tagged_migration():
    migration = tag_migration_from_diff(_empty_diff())
    assert isinstance(migration, TaggedMigration)
    assert migration.tagged == []


def test_added_table_produces_low_risk_statement():
    from pg_diff_cli.schema_fetcher import TableSchema

    table = TableSchema(name="users", columns={"id": _col("id", "integer")})
    diff = SchemaDiff(
        added_tables={"users": table},
        removed_tables={},
        modified_tables={},
    )
    migration = tag_migration_from_diff(diff)
    assert any(t.risk == RiskLevel.LOW for t in migration.tagged)


def test_removed_table_produces_high_risk_statement():
    from pg_diff_cli.schema_fetcher import TableSchema

    table = TableSchema(name="old_table", columns={"id": _col("id", "integer")})
    diff = SchemaDiff(
        added_tables={},
        removed_tables={"old_table": table},
        modified_tables={},
    )
    migration = tag_migration_from_diff(diff)
    assert migration.has_high_risk


def test_risk_summary_keys_are_all_levels():
    migration = tag_migration_from_diff(_empty_diff())
    summary = migration.risk_summary
    assert set(summary.keys()) == {"low", "medium", "high"}


def test_risk_gate_blocks_high_risk_by_default():
    from pg_diff_cli.schema_fetcher import TableSchema

    table = TableSchema(name="old", columns={"id": _col("id")})
    diff = SchemaDiff(
        added_tables={}, removed_tables={"old": table}, modified_tables={}
    )
    migration = tag_migration_from_diff(diff)
    assert risk_gate(migration, allow_high=False) is False


def test_risk_gate_allows_high_risk_when_flag_set():
    from pg_diff_cli.schema_fetcher import TableSchema

    table = TableSchema(name="old", columns={"id": _col("id")})
    diff = SchemaDiff(
        added_tables={}, removed_tables={"old": table}, modified_tables={}
    )
    migration = tag_migration_from_diff(diff)
    assert risk_gate(migration, allow_high=True) is True


def test_sql_statements_property_returns_strings():
    from pg_diff_cli.schema_fetcher import TableSchema

    table = TableSchema(name="new_tbl", columns={"id": _col("id", "integer")})
    diff = SchemaDiff(
        added_tables={"new_tbl": table},
        removed_tables={},
        modified_tables={},
    )
    migration = tag_migration_from_diff(diff)
    for s in migration.sql_statements:
        assert isinstance(s, str)
