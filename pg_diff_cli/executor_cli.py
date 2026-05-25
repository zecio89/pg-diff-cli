"""CLI sub-command for executing a migration SQL file against a database."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pg_diff_cli.sql_executor import execute_sql
from pg_diff_cli.sql_splitter import split_sql


def build_executor_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser(
        "execute",
        help="Execute a migration SQL file against a target database",
    )
    p.add_argument("dsn", help="Target database DSN")
    p.add_argument("sql_file", help="Path to the SQL migration file")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Parse and send statements but roll back — never commit",
    )
    p.add_argument(
        "--no-stop-on-error",
        action="store_true",
        default=False,
        help="Continue executing remaining statements after an error",
    )
    return p


def run_executor_cmd(args: argparse.Namespace) -> int:
    sql_path = Path(args.sql_file)
    if not sql_path.exists():
        print(f"error: file not found: {sql_path}", file=sys.stderr)
        return 1

    raw_sql = sql_path.read_text(encoding="utf-8")
    split = split_sql(raw_sql)

    if split.is_empty():
        print("No statements found in file.")
        return 0

    result = execute_sql(
        dsn=args.dsn,
        statements=split.statements,
        dry_run=args.dry_run,
        stop_on_error=not args.no_stop_on_error,
    )

    print(result.summary())

    if not result.success:
        for err in result.errors:
            print(f"  error: {err}", file=sys.stderr)
        return 1

    return 0
