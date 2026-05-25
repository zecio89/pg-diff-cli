"""Drift detection: compare a live schema against a saved baseline snapshot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.schema_differ import SchemaDiff, diff_schemas, is_empty
from pg_diff_cli.snapshot import load_snapshot


@dataclass
class DriftResult:
    baseline_name: str
    baseline_path: str
    diff: SchemaDiff
    has_drift: bool
    table_count: int
    changed_tables: int

    def summary(self) -> str:
        if not self.has_drift:
            return f"No drift detected against baseline '{self.baseline_name}'."
        return (
            f"Drift detected against baseline '{self.baseline_name}': "
            f"{self.changed_tables} of {self.table_count} table(s) changed."
        )


def detect_drift(
    live_schema: DatabaseSchema,
    snapshot_file: str,
    baseline_name: str = "snapshot",
) -> DriftResult:
    """Compare *live_schema* against a previously saved snapshot file.

    The snapshot is treated as the *source* (expected state) and the live
    schema as the *target* (current state), so additions in the live DB
    appear as added tables/columns and removals appear as removed ones.
    """
    baseline_schema: Optional[DatabaseSchema] = load_snapshot(snapshot_file)
    if baseline_schema is None:
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")

    diff: SchemaDiff = diff_schemas(baseline_schema, live_schema)
    changed = len(diff.added_tables) + len(diff.removed_tables) + len(diff.modified_tables)
    total = len(live_schema.tables)

    return DriftResult(
        baseline_name=baseline_name,
        baseline_path=snapshot_file,
        diff=diff,
        has_drift=not is_empty(diff),
        table_count=total,
        changed_tables=changed,
    )
