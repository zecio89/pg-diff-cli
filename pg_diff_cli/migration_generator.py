"""Generates migration SQL from a SchemaDiff."""

from typing import List

from pg_diff_cli.schema_differ import ColumnDiff, SchemaDiff, TableDiff


def generate_migration(diff: SchemaDiff) -> str:
    """Return a SQL migration string for the given SchemaDiff."""
    statements: List[str] = []

    for table_diff in diff.table_diffs:
        statements.extend(_statements_for_table(table_diff))

    if not statements:
        return "-- No changes detected\n"

    return "\n".join(statements) + "\n"


def _statements_for_table(table_diff: TableDiff) -> List[str]:
    stmts: List[str] = []

    if table_diff.kind == "added":
        stmts.append(f"-- Table '{table_diff.table}' was added (manual creation required)")
        return stmts

    if table_diff.kind == "removed":
        stmts.append(f"DROP TABLE IF EXISTS {table_diff.table};")
        return stmts

    for col_diff in table_diff.column_diffs:
        stmts.extend(_statements_for_column(table_diff.table, col_diff))

    return stmts


def _statements_for_column(table: str, col_diff: ColumnDiff) -> List[str]:
    stmts: List[str] = []

    if col_diff.kind == "added":
        col = col_diff.new_column
        nullable = "" if col.is_nullable else " NOT NULL"
        stmts.append(f"ALTER TABLE {table} ADD COLUMN {col.column_name} {col.data_type}{nullable};")

    elif col_diff.kind == "removed":
        stmts.append(f"ALTER TABLE {table} DROP COLUMN {col_diff.column};")

    elif col_diff.kind == "modified":
        old, new = col_diff.old_column, col_diff.new_column
        if old.data_type != new.data_type:
            stmts.append(
                f"ALTER TABLE {table} ALTER COLUMN {new.column_name} TYPE {new.data_type};"
            )
        if old.is_nullable != new.is_nullable:
            if new.is_nullable:
                stmts.append(f"ALTER TABLE {table} ALTER COLUMN {new.column_name} DROP NOT NULL;")
            else:
                stmts.append(f"ALTER TABLE {table} ALTER COLUMN {new.column_name} SET NOT NULL;")

    return stmts
