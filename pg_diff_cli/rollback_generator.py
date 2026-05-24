"""Generate rollback (undo) SQL from a SchemaDiff."""

from typing import List
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff


def generate_rollback(diff: SchemaDiff) -> str:
    """Return SQL that undoes the changes described in *diff*.

    The rollback is the logical inverse of the forward migration:
    - Added tables  → DROP TABLE
    - Removed tables → CREATE TABLE (restored)
    - Added columns  → DROP COLUMN
    - Removed columns → ADD COLUMN (restored)
    - Modified columns → ALTER COLUMN back to the *old* definition
    """
    statements: List[str] = []

    for table_name, table_diff in diff.added_tables.items():
        statements.append(f"DROP TABLE IF EXISTS {table_name};")

    for table_name, table_diff in diff.removed_tables.items():
        col_defs = ", ".join(
            f"{c.name} {c.data_type}" for c in table_diff.columns.values()
        )
        statements.append(f"CREATE TABLE {table_name} ({col_defs});")

    for table_name, table_diff in diff.modified_tables.items():
        for stmt in _rollback_statements_for_table(table_name, table_diff):
            statements.append(stmt)

    if not statements:
        return "-- No changes to roll back\n"

    return "\n".join(statements) + "\n"


def _rollback_statements_for_table(table_name: str, table_diff: TableDiff) -> List[str]:
    stmts: List[str] = []

    for col_name in table_diff.added_columns:
        stmts.append(
            f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col_name};"
        )

    for col_name, col in table_diff.removed_columns.items():
        stmts.append(
            f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col.data_type};"
        )

    for col_name, col_diff in table_diff.modified_columns.items():
        stmts.extend(_rollback_statements_for_column(table_name, col_name, col_diff))

    return stmts


def _rollback_statements_for_column(
    table_name: str, col_name: str, col_diff: ColumnDiff
) -> List[str]:
    stmts: List[str] = []

    if col_diff.old_type and col_diff.new_type:
        stmts.append(
            f"ALTER TABLE {table_name} ALTER COLUMN {col_name} "
            f"TYPE {col_diff.old_type};"
        )

    if col_diff.old_nullable is not None and col_diff.new_nullable is not None:
        constraint = "DROP NOT NULL" if col_diff.old_nullable else "SET NOT NULL"
        stmts.append(
            f"ALTER TABLE {table_name} ALTER COLUMN {col_name} {constraint};"
        )

    if col_diff.old_default != col_diff.new_default:
        if col_diff.old_default is None:
            stmts.append(
                f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP DEFAULT;"
            )
        else:
            stmts.append(
                f"ALTER TABLE {table_name} ALTER COLUMN {col_name} "
                f"SET DEFAULT {col_diff.old_default};"
            )

    return stmts
