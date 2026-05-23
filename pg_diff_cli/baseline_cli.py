"""CLI sub-commands for baseline management (save / load / list / diff)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pg_diff_cli.baseline import (
    DEFAULT_BASELINE_DIR,
    diff_against_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from pg_diff_cli.migration_generator import generate_migration
from pg_diff_cli.reporter import ReportOptions, format_report
from pg_diff_cli.schema_fetcher import fetch_schema


def build_baseline_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register 'baseline' sub-commands onto *parent*."""
    p = parent.add_parser("baseline", help="Manage schema baselines")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    # save
    save_p = sub.add_parser("save", help="Save current schema as a named baseline")
    save_p.add_argument("name", help="Baseline name")
    save_p.add_argument("--dsn", required=True, help="Connection DSN")
    save_p.add_argument("--schema", default="public", help="PostgreSQL schema name")
    save_p.add_argument("--dir", default=str(DEFAULT_BASELINE_DIR), dest="directory")

    # list
    list_p = sub.add_parser("list", help="List saved baselines")
    list_p.add_argument("--dir", default=str(DEFAULT_BASELINE_DIR), dest="directory")

    # diff
    diff_p = sub.add_parser("diff", help="Diff live schema against a baseline")
    diff_p.add_argument("name", help="Baseline name to compare against")
    diff_p.add_argument("--dsn", required=True, help="Connection DSN")
    diff_p.add_argument("--schema", default="public", help="PostgreSQL schema name")
    diff_p.add_argument("--dir", default=str(DEFAULT_BASELINE_DIR), dest="directory")
    diff_p.add_argument("--sql", action="store_true", help="Output migration SQL instead of report")


def run_baseline_cmd(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate baseline sub-command. Returns exit code."""
    directory = Path(args.directory)

    if args.baseline_cmd == "save":
        schema = fetch_schema(args.dsn, args.schema)
        path = save_baseline(schema, args.name, directory)
        print(f"Baseline '{args.name}' saved to {path}")
        return 0

    if args.baseline_cmd == "list":
        entries = list_baselines(directory)
        if not entries:
            print("No baselines found.")
        for entry in entries:
            print(f"  {entry.name}  ({entry.path})")
        return 0

    if args.baseline_cmd == "diff":
        current = fetch_schema(args.dsn, args.schema)
        diff = diff_against_baseline(current, args.name, directory)
        if args.sql:
            print(generate_migration(diff))
        else:
            opts = ReportOptions(color=sys.stdout.isatty())
            print(format_report(diff, opts))
        return 0 if _diff_is_empty(diff) else 2

    print(f"Unknown baseline command: {args.baseline_cmd}", file=sys.stderr)
    return 1


def _diff_is_empty(diff: object) -> bool:
    from pg_diff_cli.schema_differ import is_empty
    return is_empty(diff)  # type: ignore[arg-type]
