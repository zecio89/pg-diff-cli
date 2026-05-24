"""Integrate schema filtering into the fetch-diff pipeline."""
from __future__ import annotations

from typing import Optional, Tuple

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.schema_filter import FilterOptions, apply_filter
from pg_diff_cli.schema_differ import SchemaDiff, diff_schemas


def fetch_and_filter(
    source: DatabaseSchema,
    target: DatabaseSchema,
    opts: Optional[FilterOptions],
) -> Tuple[DatabaseSchema, DatabaseSchema]:
    """Apply filter to both schemas before diffing."""
    filtered_source = apply_filter(source, opts)
    filtered_target = apply_filter(target, opts)
    return filtered_source, filtered_target


def filtered_diff(
    source: DatabaseSchema,
    target: DatabaseSchema,
    opts: Optional[FilterOptions],
) -> SchemaDiff:
    """Convenience: filter both schemas then compute the diff."""
    filtered_source, filtered_target = fetch_and_filter(source, target, opts)
    return diff_schemas(filtered_source, filtered_target)


def summarize_filter(opts: Optional[FilterOptions]) -> str:
    """Return a human-readable summary of active filter rules."""
    if opts is None:
        return "No table/schema filters active."
    parts = []
    if opts.include_tables:
        parts.append(f"include tables: {', '.join(opts.include_tables)}")
    if opts.exclude_tables:
        parts.append(f"exclude tables: {', '.join(opts.exclude_tables)}")
    if opts.include_schemas:
        parts.append(f"include schemas: {', '.join(opts.include_schemas)}")
    if opts.exclude_schemas:
        parts.append(f"exclude schemas: {', '.join(opts.exclude_schemas)}")
    return "Filters active — " + "; ".join(parts) + "."
