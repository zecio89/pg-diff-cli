"""CLI sub-command: drift  — detect schema drift against a snapshot."""
from __future__ import annotations

import argparse
import sys
from typing import List

from pg_diff_cli.drift_detector import detect_drift
from pg_diff_cli.reporter import format_report, ReportOptions
from pg_diff_cli.schema_fetcher import fetch_schema


def build_drift_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "drift",
        help="Compare a live database schema against a saved snapshot.",
    )
    p.add_argument("dsn", help="DSN of the live PostgreSQL database.")
    p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p.add_argument(
        "--baseline-name",
        default="snapshot",
        help="Label used in output messages (default: snapshot).",
    )
    p.add_argument(
        "--schema",
        default="public",
        help="PostgreSQL schema to inspect (default: public).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour in output.",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 2 when drift is found (useful in CI).",
    )
    return p


def run_drift_cmd(args: argparse.Namespace) -> int:
    """Execute the drift sub-command.  Returns an integer exit code."""
    try:
        live = fetch_schema(args.dsn, schema=args.schema)
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: could not connect to database: {exc}", file=sys.stderr)
        return 1

    try:
        result = detect_drift(
            live_schema=live,
            snapshot_file=args.snapshot,
            baseline_name=args.baseline_name,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    opts = ReportOptions(color=not args.no_color)
    report = format_report(result.diff, opts)
    print(result.summary())
    print(report)

    if args.exit_code and result.has_drift:
        return 2
    return 0
