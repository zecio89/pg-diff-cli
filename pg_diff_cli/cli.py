"""CLI entry-point for pg-diff-cli."""

from __future__ import annotations

import argparse
import sys

from pg_diff_cli.config import DiffConfig, validate
from pg_diff_cli.schema_fetcher import fetch_schema
from pg_diff_cli.schema_differ import diff_schemas, is_empty
from pg_diff_cli.migration_generator import generate_migration
from pg_diff_cli.reporter import ReportOptions, print_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pg-diff",
        description="Diff two PostgreSQL schemas and output migration SQL.",
    )
    parser.add_argument("--source", required=True, help="Source database DSN")
    parser.add_argument("--target", required=True, help="Target database DSN")
    parser.add_argument(
        "--schema", default="public", help="Schema name to compare (default: public)"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show column details for added/removed tables"
    )
    parser.add_argument(
        "--sql", action="store_true", help="Output migration SQL instead of human-readable report"
    )
    return parser


def run(args: argparse.Namespace) -> int:
    config = DiffConfig(
        source_dsn=args.source,
        target_dsn=args.target,
        schema=args.schema,
    )
    try:
        validate(config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    source_schema = fetch_schema(config.source_dsn, config.schema)
    target_schema = fetch_schema(config.target_dsn, config.schema)

    diff = diff_schemas(source_schema, target_schema)

    if args.sql:
        sql = generate_migration(diff)
        print(sql)
    else:
        opts = ReportOptions(color=not args.no_color, verbose=args.verbose)
        print_report(diff, opts)

    return 0 if is_empty(diff) else 2


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
