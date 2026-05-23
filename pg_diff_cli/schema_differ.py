"""Compares two DatabaseSchema objects and produces a list of SchemaDiff objects."""

from dataclasses import dataclass, field
from typing import List

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema


@dataclass
class ColumnDiff:
    table: str
    column: str
    kind: str  # 'added', 'removed', 'modified'
    old_column: TableColumn | None = None
    new_column: TableColumn | None = None


@dataclass
class TableDiff:
    table: str
    kind: str  # 'added', 'removed', 'modified'
    column_diffs: List[ColumnDiff] = field(default_factory=list)


@dataclass
class SchemaDiff:
    table_diffs: List[TableDiff] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.table_diffs) == 0


def diff_schemas(source: DatabaseSchema, target: DatabaseSchema) -> SchemaDiff:
    """Return a SchemaDiff describing changes needed to migrate source -> target."""
    table_diffs: List[TableDiff] = []

    source_tables = {t.table_name: t for t in source.tables}
    target_tables = {t.table_name: t for t in target.tables}

    for name in sorted(target_tables.keys() - source_tables.keys()):
        table_diffs.append(TableDiff(table=name, kind="added"))

    for name in sorted(source_tables.keys() - target_tables.keys()):
        table_diffs.append(TableDiff(table=name, kind="removed"))

    for name in sorted(source_tables.keys() & target_tables.keys()):
        col_diffs = _diff_columns(name, source_tables[name], target_tables[name])
        if col_diffs:
            table_diffs.append(TableDiff(table=name, kind="modified", column_diffs=col_diffs))

    return SchemaDiff(table_diffs=table_diffs)


def _diff_columns(
    table_name: str, source: TableSchema, target: TableSchema
) -> List[ColumnDiff]:
    diffs: List[ColumnDiff] = []
    src_cols = {c.column_name: c for c in source.columns}
    tgt_cols = {c.column_name: c for c in target.columns}

    for col in sorted(tgt_cols.keys() - src_cols.keys()):
        diffs.append(ColumnDiff(table=table_name, column=col, kind="added", new_column=tgt_cols[col]))

    for col in sorted(src_cols.keys() - tgt_cols.keys()):
        diffs.append(ColumnDiff(table=table_name, column=col, kind="removed", old_column=src_cols[col]))

    for col in sorted(src_cols.keys() & tgt_cols.keys()):
        s, t = src_cols[col], tgt_cols[col]
        if s.data_type != t.data_type or s.is_nullable != t.is_nullable:
            diffs.append(
                ColumnDiff(table=table_name, column=col, kind="modified", old_column=s, new_column=t)
            )

    return diffs
