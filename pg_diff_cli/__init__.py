"""pg-diff-cli: PostgreSQL schema diff and migration generator."""

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema, fetch_schema
from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff, diff_schemas
from pg_diff_cli.migration_generator import generate_migration

__all__ = [
    "DatabaseSchema",
    "TableColumn",
    "TableSchema",
    "fetch_schema",
    "SchemaDiff",
    "TableDiff",
    "ColumnDiff",
    "diff_schemas",
    "generate_migration",
]
