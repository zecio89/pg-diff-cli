"""High-level helpers that combine fetching + exporting in one call."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pg_diff_cli.schema_exporter import ExportFormat, ExportResult, export_schema
from pg_diff_cli.snapshot import load_snapshot, save_snapshot
from pg_diff_cli.schema_fetcher import DatabaseSchema


class ExportBundle:
    """Holds the schema and the rendered export content together."""

    def __init__(self, schema: DatabaseSchema, result: ExportResult) -> None:
        self.schema = schema
        self.result = result

    @property
    def table_count(self) -> int:
        return len(self.schema.tables)

    @property
    def column_count(self) -> int:
        return sum(len(t.columns) for t in self.schema.tables.values())

    def summary(self) -> str:
        return (
            f"{self.table_count} table(s), "
            f"{self.column_count} column(s) — "
            f"{len(self.result)} bytes ({self.result.format.value})"
        )


def export_from_snapshot(
    snapshot_path: Path,
    fmt: ExportFormat = ExportFormat.JSON,
    indent: int = 2,
) -> Optional[ExportBundle]:
    """Load a snapshot file and export it.  Returns *None* on failure."""
    schema = load_snapshot(snapshot_path)
    if schema is None:
        return None
    result = export_schema(schema, fmt=fmt, indent=indent)
    return ExportBundle(schema, result)


def export_and_save(
    schema: DatabaseSchema,
    output_path: Path,
    fmt: ExportFormat = ExportFormat.JSON,
    indent: int = 2,
) -> ExportBundle:
    """Export *schema* and write the result to *output_path*."""
    result = export_schema(schema, fmt=fmt, indent=indent)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.content, encoding="utf-8")
    return ExportBundle(schema, result)
