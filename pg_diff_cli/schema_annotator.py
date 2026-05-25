"""Attach human-readable annotations to schema objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff


@dataclass
class ColumnAnnotation:
    table: str
    column: str
    note: str


@dataclass
class TableAnnotation:
    table: str
    note: str
    column_notes: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnnotatedSchema:
    schema: DatabaseSchema
    table_annotations: Dict[str, TableAnnotation] = field(default_factory=dict)

    def annotate_table(self, table: str, note: str) -> None:
        ann = self.table_annotations.setdefault(table, TableAnnotation(table=table, note=""))
        ann.note = note

    def annotate_column(self, table: str, column: str, note: str) -> None:
        ann = self.table_annotations.setdefault(table, TableAnnotation(table=table, note=""))
        ann.column_notes[column] = note

    def get_table_note(self, table: str) -> Optional[str]:
        ann = self.table_annotations.get(table)
        return ann.note if ann and ann.note else None

    def get_column_note(self, table: str, column: str) -> Optional[str]:
        ann = self.table_annotations.get(table)
        if ann:
            return ann.column_notes.get(column)
        return None


def annotate_diff(diff: SchemaDiff, annotated: AnnotatedSchema) -> List[str]:
    """Return annotation lines relevant to the tables affected by *diff*."""
    lines: List[str] = []
    affected = set()
    for td in diff.added_tables + diff.removed_tables + diff.modified_tables:
        affected.add(td.table_name)

    for table in sorted(affected):
        note = annotated.get_table_note(table)
        if note:
            lines.append(f"-- [{table}] {note}")
        td = _find_table_diff(diff, table)
        if td:
            for cd in td.added_columns + td.removed_columns + td.modified_columns:
                col_note = annotated.get_column_note(table, cd.column_name)
                if col_note:
                    lines.append(f"--   [{table}.{cd.column_name}] {col_note}")
    return lines


def _find_table_diff(diff: SchemaDiff, table_name: str) -> Optional[TableDiff]:
    for td in diff.added_tables + diff.removed_tables + diff.modified_tables:
        if td.table_name == table_name:
            return td
    return None
