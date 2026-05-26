"""Compact summary statistics derived from a SchemaDiff."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pg_diff_cli.schema_differ import SchemaDiff, TableDiff


@dataclass
class TableSummary:
    name: str
    added: bool = False
    removed: bool = False
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0

    @property
    def has_changes(self) -> bool:
        return (
            self.added
            or self.removed
            or self.columns_added > 0
            or self.columns_removed > 0
            or self.columns_modified > 0
        )


@dataclass
class DiffSummary:
    tables_added: int = 0
    tables_removed: int = 0
    tables_modified: int = 0
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0
    table_details: List[TableSummary] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (
            self.tables_added
            + self.tables_removed
            + self.tables_modified
            + self.columns_added
            + self.columns_removed
            + self.columns_modified
        )

    @property
    def is_empty(self) -> bool:
        return self.total_changes == 0

    def as_text(self) -> str:
        if self.is_empty:
            return "No schema differences found."
        lines = [
            f"Tables added:    {self.tables_added}",
            f"Tables removed:  {self.tables_removed}",
            f"Tables modified: {self.tables_modified}",
            f"Columns added:   {self.columns_added}",
            f"Columns removed: {self.columns_removed}",
            f"Columns changed: {self.columns_modified}",
        ]
        return "\n".join(lines)


def _summarize_table(td: TableDiff) -> TableSummary:
    ts = TableSummary(name=td.table_name, added=td.added, removed=td.removed)
    for cd in td.column_diffs:
        if cd.added:
            ts.columns_added += 1
        elif cd.removed:
            ts.columns_removed += 1
        else:
            ts.columns_modified += 1
    return ts


def summarize_diff(diff: SchemaDiff) -> DiffSummary:
    """Compute a DiffSummary from a SchemaDiff."""
    summary = DiffSummary()
    for td in diff.table_diffs:
        ts = _summarize_table(td)
        summary.table_details.append(ts)
        if ts.added:
            summary.tables_added += 1
        elif ts.removed:
            summary.tables_removed += 1
        else:
            summary.tables_modified += 1
        summary.columns_added += ts.columns_added
        summary.columns_removed += ts.columns_removed
        summary.columns_modified += ts.columns_modified
    return summary
