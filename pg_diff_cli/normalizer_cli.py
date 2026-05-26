"""CLI subcommand for normalizing SQL input."""

from __future__ import annotations

import argparse
import sys
from typing import List

from pg_diff_cli.sql_normalizer import NormalizeOptions, normalize_statements
from pg_diff_cli.sql_splitter import split_sql


def build_normalizer_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Normalize SQL statements for consistent formatting."
    if subparsers is not None:
        parser = subparsers.add_parser("normalize", help=description)
    else:
        parser = argparse.ArgumentParser(prog="pg-diff normalize", description=description)

    parser.add_argument("file", nargs="?", default="-", help="SQL file to normalize (default: stdin)")
    parser.add_argument("--no-uppercase", action="store_true", help="Skip keyword uppercasing")
    parser.add_argument("--remove-comments", action="store_true", help="Strip inline SQL comments")
    parser.add_argument("--show-changes", action="store_true", help="Print a summary of changes made")
    return parser


def _read_sql(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def run_normalizer_cmd(args: argparse.Namespace) -> int:
    try:
        raw = _read_sql(args.file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    split = split_sql(raw)
    if split.is_empty:
        print("-- no statements found")
        return 0

    options = NormalizeOptions(
        uppercase_keywords=not args.no_uppercase,
        remove_inline_comments=args.remove_comments,
    )

    results = normalize_statements(split.statements, options)
    output_parts: List[str] = []

    for res in results:
        output_parts.append(res.normalized + ";")
        if args.show_changes and res.changes:
            for change in res.changes:
                output_parts.append(f"-- [{change}]")

    print("\n".join(output_parts))
    return 0
