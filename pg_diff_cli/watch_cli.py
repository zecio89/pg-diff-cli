"""CLI sub-command: pg-diff watch — continuously poll and report schema diffs."""

from __future__ import annotations

import argparse
import sys
from typing import List

from pg_diff_cli.reporter import ReportOptions, format_report
from pg_diff_cli.schema_differ import SchemaDiff, is_empty
from pg_diff_cli.watch import WatchOptions, run_watch


def build_watch_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Poll two schemas repeatedly and print diffs as they appear.",
    )
    p.add_argument("source_dsn", help="DSN for the source database")
    p.add_argument("target_dsn", help="DSN for the target database")
    p.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Seconds between polls (default: 30)",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N polls (0 = run forever, default: 0)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    return p


def _make_diff_handler(no_color: bool, out=sys.stdout) -> object:
    iteration = [0]

    def on_diff(diff: SchemaDiff) -> None:
        iteration[0] += 1
        opts = ReportOptions(color=not no_color)
        header = f"\n=== Poll #{iteration[0]} — changes detected ==="
        print(header, file=out)
        print(format_report(diff, opts), file=out)

    return on_diff


def run_watch_cmd(args: argparse.Namespace, out=sys.stdout) -> int:
    no_color: bool = getattr(args, "no_color", False)
    on_diff = _make_diff_handler(no_color, out)

    def on_no_change() -> None:
        print("[watch] No schema changes detected.", file=out)

    options = WatchOptions(
        source_dsn=args.source_dsn,
        target_dsn=args.target_dsn,
        interval=args.interval,
        max_iterations=args.max_iterations,
        on_diff=on_diff,  # type: ignore[arg-type]
        on_no_change=on_no_change,
    )

    try:
        run_watch(options)
    except KeyboardInterrupt:
        print("\n[watch] Interrupted.", file=out)

    return 0
