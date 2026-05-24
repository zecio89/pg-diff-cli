"""Tests for pg_diff_cli.plan_exporter."""
import json

import pytest

from pg_diff_cli.plan_exporter import MigrationPlan, PlanMeta, PlanStep, build_plan
from pg_diff_cli.schema_differ import ColumnDiff, SchemaDiff, TableDiff
from pg_diff_cli.schema_fetcher import TableColumn


def _col(name="id", col_type="integer", nullable=False) -> TableColumn:
    return TableColumn(name=name, col_type=col_type, nullable=nullable, default=None)


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables={}, removed_tables={}, modified_tables={})


def test_empty_diff_produces_empty_plan():
    plan = build_plan(_empty_diff())
    assert plan.is_empty()
    assert plan.steps == []


def test_added_table_creates_add_table_step():
    from pg_diff_cli.schema_fetcher import TableSchema
    diff = SchemaDiff(
        added_tables={"users": TableSchema(name="users", columns={"id": _col()})},
        removed_tables={},
        modified_tables={},
    )
    plan = build_plan(diff)
    assert len(plan.steps) == 1
    assert plan.steps[0].operation == "add_table"
    assert plan.steps[0].table == "users"


def test_removed_table_creates_drop_table_step():
    from pg_diff_cli.schema_fetcher import TableSchema
    diff = SchemaDiff(
        added_tables={},
        removed_tables={"orders": TableSchema(name="orders", columns={})},
        modified_tables={},
    )
    plan = build_plan(diff)
    assert plan.steps[0].operation == "drop_table"
    assert plan.steps[0].table == "orders"


def test_added_column_step():
    td = TableDiff(
        table_name="products",
        added_columns={"price": _col("price", "numeric")},
        removed_columns={},
        modified_columns={},
    )
    diff = SchemaDiff(added_tables={}, removed_tables={}, modified_tables={"products": td})
    plan = build_plan(diff)
    assert any(s.operation == "add_column" and s.column == "price" for s in plan.steps)


def test_alter_column_includes_detail():
    cd = ColumnDiff(
        column_name="amount",
        old_type="integer",
        new_type="numeric",
        old_nullable=False,
        new_nullable=True,
    )
    td = TableDiff(
        table_name="invoices",
        added_columns={},
        removed_columns={},
        modified_columns={"amount": cd},
    )
    diff = SchemaDiff(added_tables={}, removed_tables={}, modified_tables={"invoices": td})
    plan = build_plan(diff)
    step = plan.steps[0]
    assert step.operation == "alter_column"
    assert "integer" in step.detail
    assert "numeric" in step.detail


def test_to_json_is_valid_json():
    plan = build_plan(_empty_diff(), meta=PlanMeta(source_dsn="postgres://localhost/a"))
    raw = plan.to_json()
    data = json.loads(raw)
    assert "steps" in data
    assert "meta" in data


def test_plan_meta_stored_on_plan():
    meta = PlanMeta(source_dsn="src", target_dsn="tgt", schema_name="public")
    plan = build_plan(_empty_diff(), meta=meta)
    assert plan.meta.source_dsn == "src"
    assert plan.meta.schema_name == "public"
