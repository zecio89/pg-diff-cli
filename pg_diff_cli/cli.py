"""Command-line interface for pg-diff-cli."""

import sys
import argparse

from pg_diff_cli.schema_fetcher import fetch_schema
from pg_diff_cli.schema_differ import diff_schemas, is_empty
from pg_diff_cli.migration_generator import generate_migration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pg-diff",
        description="Diff two PostgreSQL schemas and output migration SQL.",
    )
    parser.add_argument(
        "source_dsn",
        help="DSN for the source (current) database, e.g. postgresql://user:pass@host/db",
    )
    parser.add_argument(
        "target_dsn",
        help="DSN for the target (desired) database, e.g. postgresql://user:pass@host/db",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Write migration SQL to FILE instead of stdout.",
    )
    parser.add_argument(
        "--schema",
        "-s",
        metavar="SCHEMA",
        default="public",
        help="PostgreSQL schema name to inspect (default: public).",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        default=False,
        help="Suppress the informational comment header in the output.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Entry point; returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        source_schema = fetch_schema(args.source_dsn, schema=args.schema)
        target_schema = fetch_schema(args.target_dsn, schema=args.schema)
    except Exception as exc:  # noqa: BLE001
        print(f"Error connecting to database: {exc}", file=sys.stderr)
        return 1

    diff = diff_schemas(source_schema, target_schema)
    sql = generate_migration(diff, include_header=not args.no_header)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(sql)
            print(f"Migration written to {args.output}")
        except OSError as exc:
            print(f"Error writing output file: {exc}", file=sys.stderr)
            return 1
    else:
        print(sql)

    return 0 if is_empty(diff) else 2


def main() -> None:  # pragma: no cover
    sys.exit(run())
