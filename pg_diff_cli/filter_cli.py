"""CLI helpers for --include-table / --exclude-table / schema filter flags."""
from __future__ import annotations

import argparse
from typing import Optional

from pg_diff_cli.schema_filter import FilterOptions


def add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach filter-related flags to an existing ArgumentParser."""
    grp = parser.add_argument_group("schema filtering")
    grp.add_argument(
        "--include-table",
        metavar="PATTERN",
        action="append",
        dest="include_tables",
        default=[],
        help="Include only tables matching PATTERN (fnmatch, repeatable).",
    )
    grp.add_argument(
        "--exclude-table",
        metavar="PATTERN",
        action="append",
        dest="exclude_tables",
        default=[],
        help="Exclude tables matching PATTERN (fnmatch, repeatable).",
    )
    grp.add_argument(
        "--include-schema",
        metavar="PATTERN",
        action="append",
        dest="include_schemas",
        default=[],
        help="Include only schemas matching PATTERN (fnmatch, repeatable).",
    )
    grp.add_argument(
        "--exclude-schema",
        metavar="PATTERN",
        action="append",
        dest="exclude_schemas",
        default=[],
        help="Exclude schemas matching PATTERN (fnmatch, repeatable).",
    )


def filter_options_from_args(args: argparse.Namespace) -> Optional[FilterOptions]:
    """Build FilterOptions from parsed CLI args; returns None when no filters set."""
    opts = FilterOptions(
        include_tables=getattr(args, "include_tables", []) or [],
        exclude_tables=getattr(args, "exclude_tables", []) or [],
        include_schemas=getattr(args, "include_schemas", []) or [],
        exclude_schemas=getattr(args, "exclude_schemas", []) or [],
    )
    if not any([opts.include_tables, opts.exclude_tables, opts.include_schemas, opts.exclude_schemas]):
        return None
    return opts
