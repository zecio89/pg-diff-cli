"""CLI sub-command: rollback — generate undo SQL for a diff."""

import argparse
import sys
from typing import Optional

from pg_diff_cli.schema_fetcher import fetch_schema
from pg_diff_cli.schema_differ import diff_schemas
from pg_diff_cli.rollback_generator import generate_rollback
from pg_diff_cli.output_writer import write_output


def build_rollback_parser(subparsers=None) -> argparse.ArgumentParser:
    """Return (or attach) the argument parser for the *rollback* sub-command."""
    description = "Generate rollback SQL that undoes a forward migration."

    if subparsers is not None:
        parser = subparsers.add_parser("rollback", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="pg-diff rollback", description=description
        )

    parser.add_argument(
        "source_dsn",
        help="DSN of the source (original) database.",
    )
    parser.add_argument(
        "target_dsn",
        help="DSN of the target (migrated) database.",
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="PostgreSQL schema name to compare (default: public).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write rollback SQL to FILE instead of stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print rollback SQL without semicolons (safe preview).",
    )
    return parser


def run_rollback_cmd(args: argparse.Namespace, out=None) -> int:
    """Execute the rollback sub-command.  Returns an exit code.

    Exit codes:
      0 — no changes detected (nothing to roll back)
      2 — rollback SQL generated successfully
      1 — error
    """
    if out is None:
        out = sys.stdout

    try:
        source = fetch_schema(args.source_dsn, schema=args.schema)
        target = fetch_schema(args.target_dsn, schema=args.schema)
    except Exception as exc:  # pragma: no cover
        print(f"Error fetching schema: {exc}", file=sys.stderr)
        return 1

    diff = diff_schemas(source, target)
    sql = generate_rollback(diff)

    if args.dry_run:
        sql = sql.replace(";", "")

    if args.output:
        write_output(sql, path=args.output)
    else:
        out.write(sql)

    no_changes = sql.strip().startswith("-- No changes")
    return 0 if no_changes else 2
