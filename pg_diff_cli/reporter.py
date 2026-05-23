"""Human-readable reporting of schema diffs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO
import sys

from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff


@dataclass
class ReportOptions:
    color: bool = True
    verbose: bool = False


_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"


def _c(text: str, code: str, use_color: bool) -> str:
    return f"{code}{text}{_RESET}" if use_color else text


def _summarize_column(col: ColumnDiff, opts: ReportOptions) -> list[str]:
    lines: list[str] = []
    name = col.column_name
    if col.added:
        lines.append(_c(f"    + column {name} ({col.new_type})", _GREEN, opts.color))
    elif col.removed:
        lines.append(_c(f"    - column {name} ({col.old_type})", _RED, opts.color))
    else:
        if col.type_changed:
            lines.append(
                _c(f"    ~ column {name}: type {col.old_type} -> {col.new_type}", _YELLOW, opts.color)
            )
        if col.nullable_changed:
            lines.append(
                _c(f"    ~ column {name}: nullable {col.old_nullable} -> {col.new_nullable}", _YELLOW, opts.color)
            )
    return lines


def _summarize_table(table: TableDiff, opts: ReportOptions) -> list[str]:
    lines: list[str] = []
    if table.added:
        lines.append(_c(f"  + table {table.table_name}", _GREEN, opts.color))
    elif table.removed:
        lines.append(_c(f"  - table {table.table_name}", _RED, opts.color))
    else:
        lines.append(_c(f"  ~ table {table.table_name}", _YELLOW, opts.color))
    if opts.verbose or not (table.added or table.removed):
        for col in table.column_diffs:
            lines.extend(_summarize_column(col, opts))
    return lines


def format_report(diff: SchemaDiff, opts: ReportOptions | None = None) -> str:
    """Return a formatted string report of *diff*."""
    if opts is None:
        opts = ReportOptions()

    if not diff.table_diffs:
        return _c("No schema differences found.", _BOLD, opts.color)

    lines = [_c("Schema differences:", _BOLD, opts.color)]
    for table in diff.table_diffs:
        lines.extend(_summarize_table(table, opts))
    total = len(diff.table_diffs)
    lines.append(f"\n{total} table(s) with differences.")
    return "\n".join(lines)


def print_report(diff: SchemaDiff, opts: ReportOptions | None = None, file: TextIO = sys.stdout) -> None:
    """Print the formatted report to *file*."""
    print(format_report(diff, opts), file=file)
