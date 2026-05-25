"""High-level helpers that combine annotations with diff output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pg_diff_cli.schema_differ import SchemaDiff
from pg_diff_cli.schema_annotator import AnnotatedSchema, annotate_diff


@dataclass
class AnnotatedMigration:
    """Pairs migration SQL with annotation comment lines."""
    sql: str
    annotation_lines: List[str]

    def full_output(self) -> str:
        """Return annotation comments followed by the SQL."""
        if not self.annotation_lines:
            return self.sql
        header = "\n".join(self.annotation_lines)
        return f"{header}\n\n{self.sql}"

    @property
    def has_annotations(self) -> bool:
        return bool(self.annotation_lines)


def build_annotated_migration(
    diff: SchemaDiff,
    sql: str,
    annotated: Optional[AnnotatedSchema] = None,
) -> AnnotatedMigration:
    """Combine *sql* with annotation lines derived from *diff* and *annotated*."""
    if annotated is None:
        return AnnotatedMigration(sql=sql, annotation_lines=[])
    lines = annotate_diff(diff, annotated)
    return AnnotatedMigration(sql=sql, annotation_lines=lines)


def annotation_summary(annotated: AnnotatedSchema) -> str:
    """Return a short human-readable summary of all stored annotations."""
    if not annotated.table_annotations:
        return "No annotations defined."
    parts: List[str] = []
    for table in sorted(annotated.table_annotations):
        info = annotated.table_annotations[table]
        note_str = f": {info.note}" if info.note else ""
        parts.append(f"  {table}{note_str}")
        for col, cnote in sorted(info.column_notes.items()):
            parts.append(f"    .{col}: {cnote}")
    return "Annotations:\n" + "\n".join(parts)
