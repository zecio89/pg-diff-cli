"""CLI entry point for pg-diff-cli."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from pg_diff_cli.config import DiffConfig, validate
from pg_diff_cli.schema_fetcher import fetch_schema
from pg_diff_cli.schema_differ import diff_schemas, is_empty
from pg_diff_cli.migration_generator import generate_migration
from pg_diff_cli.reporter import format_report, ReportOptions
from pg_diff_cli.snapshot import save_snapshot, load_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pg-diff",
        description="Diff two PostgreSQL schemas and output migration SQL.",
    )
    parser.add_argument("source", help="Source DSN (e.g. postgresql://user:pass@host/db)")
    parser.add_argument("target", help="Target DSN")
    parser.add_argument("--schema", default="public", help="Schema name (default: public)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--quiet", action="store_true", help="Suppress report; only emit SQL")
    parser.add_argument(
        "--save-snapshot",
        metavar="FILE",
        help="Save the source schema snapshot to FILE after fetching",
    )
    parser.add_argument(
        "--load-snapshot",
        metavar="FILE",
        help="Load source schema from a snapshot FILE instead of connecting",
    )
    return parser


def run(
    config: DiffConfig,
    save_snapshot_path: Optional[str] = None,
    load_snapshot_path: Optional[str] = None,
    no_color: bool = False,
    quiet: bool = False,
    out=sys.stdout,
) -> int:
    """Execute the diff and write output.  Returns an exit code."""
    if load_snapshot_path:
        source_schema = load_snapshot(load_snapshot_path)
    else:
        source_schema = fetch_schema(config.source_dsn, config.schema)

    if save_snapshot_path:
        save_snapshot(source_schema, save_snapshot_path)

    target_schema = fetch_schema(config.target_dsn, config.schema)
    diff = diff_schemas(source_schema, target_schema)

    if not quiet:
        opts = ReportOptions(color=not no_color)
        out.write(format_report(diff, opts))
        out.write("\n")

    sql = generate_migration(diff)
    out.write(sql)
    out.write("\n")

    return 0 if is_empty(diff) else 2


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = DiffConfig(
        source_dsn=args.source,
        target_dsn=args.target,
        schema=args.schema,
    )
    validate(config)
    code = run(
        config,
        save_snapshot_path=args.save_snapshot,
        load_snapshot_path=args.load_snapshot,
        no_color=args.no_color,
        quiet=args.quiet,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
