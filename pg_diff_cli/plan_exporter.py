"""Export a SchemaDiff as a structured migration plan (JSON/YAML)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List, Optional

from pg_diff_cli.schema_differ import SchemaDiff


@dataclass
class PlanMeta:
    source_dsn: Optional[str] = None
    target_dsn: Optional[str] = None
    generated_at: Optional[str] = None
    schema_name: Optional[str] = None


@dataclass
class PlanStep:
    operation: str        # 'add_table' | 'drop_table' | 'add_column' | 'drop_column' | 'alter_column'
    table: str
    column: Optional[str] = None
    detail: Optional[str] = None


@dataclass
class MigrationPlan:
    meta: PlanMeta
    steps: List[PlanStep]

    def is_empty(self) -> bool:
        return len(self.steps) == 0

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def build_plan(diff: SchemaDiff, meta: Optional[PlanMeta] = None) -> MigrationPlan:
    """Convert a SchemaDiff into a structured MigrationPlan."""
    steps: List[PlanStep] = []

    for table_name in diff.added_tables:
        steps.append(PlanStep(operation="add_table", table=table_name))

    for table_name in diff.removed_tables:
        steps.append(PlanStep(operation="drop_table", table=table_name))

    for table_name, table_diff in diff.modified_tables.items():
        for col_name in table_diff.added_columns:
            steps.append(PlanStep(operation="add_column", table=table_name, column=col_name))

        for col_name in table_diff.removed_columns:
            steps.append(PlanStep(operation="drop_column", table=table_name, column=col_name))

        for col_name, col_diff in table_diff.modified_columns.items():
            detail_parts = []
            if col_diff.old_type != col_diff.new_type:
                detail_parts.append(f"type: {col_diff.old_type} -> {col_diff.new_type}")
            if col_diff.old_nullable != col_diff.new_nullable:
                detail_parts.append(f"nullable: {col_diff.old_nullable} -> {col_diff.new_nullable}")
            steps.append(PlanStep(
                operation="alter_column",
                table=table_name,
                column=col_name,
                detail="; ".join(detail_parts) or None,
            ))

    return MigrationPlan(meta=meta or PlanMeta(), steps=steps)
