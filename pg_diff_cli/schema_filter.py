"""Filter schemas by include/exclude patterns for tables and columns."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema


@dataclass
class FilterOptions:
    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    include_schemas: List[str] = field(default_factory=list)
    exclude_schemas: List[str] = field(default_factory=list)


def _matches_any(name: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def _table_allowed(table: TableSchema, opts: FilterOptions) -> bool:
    schema_part, _, table_part = table.name.partition(".")
    if not table_part:
        schema_part, table_part = "public", schema_part

    if opts.include_schemas and not _matches_any(schema_part, opts.include_schemas):
        return False
    if opts.exclude_schemas and _matches_any(schema_part, opts.exclude_schemas):
        return False
    if opts.include_tables and not _matches_any(table.name, opts.include_tables):
        return False
    if opts.exclude_tables and _matches_any(table.name, opts.exclude_tables):
        return False
    return True


def apply_filter(schema: DatabaseSchema, opts: Optional[FilterOptions]) -> DatabaseSchema:
    """Return a new DatabaseSchema with only the allowed tables."""
    if opts is None:
        return schema
    filtered = {name: tbl for name, tbl in schema.tables.items() if _table_allowed(tbl, opts)}
    return DatabaseSchema(tables=filtered)


def filter_options_from_config(config: dict) -> FilterOptions:
    """Build FilterOptions from a plain config dict (e.g. parsed TOML/JSON)."""
    return FilterOptions(
        include_tables=config.get("include_tables", []),
        exclude_tables=config.get("exclude_tables", []),
        include_schemas=config.get("include_schemas", []),
        exclude_schemas=config.get("exclude_schemas", []),
    )
