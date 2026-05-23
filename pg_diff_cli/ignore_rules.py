"""Support for ignore rules that filter out specific tables or columns from diffs."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List

from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff


@dataclass
class IgnoreRules:
    """Rules that suppress specific tables or columns from appearing in a diff."""

    tables: List[str] = field(default_factory=list)
    """Glob patterns for table names to ignore entirely."""

    columns: List[str] = field(default_factory=list)
    """Glob patterns in the form 'table.column' to ignore specific columns."""


def _matches_any(value: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(value, pat) for pat in patterns)


def _filter_column_diffs(table_name: str, diffs: List[ColumnDiff], rules: IgnoreRules) -> List[ColumnDiff]:
    kept = []
    for cd in diffs:
        qualified = f"{table_name}.{cd.column_name}"
        if not _matches_any(qualified, rules.columns):
            kept.append(cd)
    return kept


def apply_ignore_rules(diff: SchemaDiff, rules: IgnoreRules) -> SchemaDiff:
    """Return a new SchemaDiff with ignored tables/columns removed."""
    if not rules.tables and not rules.columns:
        return diff

    filtered_added = [
        t for t in diff.added_tables
        if not _matches_any(t.table_name, rules.tables)
    ]
    filtered_removed = [
        t for t in diff.removed_tables
        if not _matches_any(t.table_name, rules.tables)
    ]

    filtered_changed: List[TableDiff] = []
    for td in diff.changed_tables:
        if _matches_any(td.table_name, rules.tables):
            continue
        new_td = TableDiff(
            table_name=td.table_name,
            added_columns=_filter_column_diffs(td.table_name, td.added_columns, rules),
            removed_columns=_filter_column_diffs(td.table_name, td.removed_columns, rules),
            changed_columns=_filter_column_diffs(td.table_name, td.changed_columns, rules),
        )
        # Only keep the table diff if something remains
        if new_td.added_columns or new_td.removed_columns or new_td.changed_columns:
            filtered_changed.append(new_td)

    return SchemaDiff(
        added_tables=filtered_added,
        removed_tables=filtered_removed,
        changed_tables=filtered_changed,
    )


def ignore_rules_from_config(cfg: dict) -> IgnoreRules:
    """Build IgnoreRules from a plain dict (e.g. loaded from TOML/JSON config)."""
    return IgnoreRules(
        tables=cfg.get("tables", []),
        columns=cfg.get("columns", []),
    )
