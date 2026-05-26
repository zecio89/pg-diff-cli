"""CLI sub-command: pg-diff summary — print compact diff statistics."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from pg_diff_cli.schema_diff_summary import DiffSummary, summarize_diff
from pg_diff_cli.schema_differ import SchemaDiff


def build_summary_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Print a compact summary of schema differences."
    if subparsers is not None:
        parser = subparsers.add_parser("summary", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="pg-diff summary", description=description)
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--show-tables",
        action="store_true",
        default=False,
        help="List each changed table individually",
    )
    return parser


def _format_json(summary: DiffSummary, show_tables: bool) -> str:
    import json

    data = {
        "tables_added": summary.tables_added,
        "tables_removed": summary.tables_removed,
        "tables_modified": summary.tables_modified,
        "columns_added": summary.columns_added,
        "columns_removed": summary.columns_removed,
        "columns_modified": summary.columns_modified,
        "total_changes": summary.total_changes,
    }
    if show_tables:
        data["tables"] = [
            {
                "name": t.name,
                "added": t.added,
                "removed": t.removed,
                "columns_added": t.columns_added,
                "columns_removed": t.columns_removed,
                "columns_modified": t.columns_modified,
            }
            for t in summary.table_details
            if t.has_changes
        ]
    return json.dumps(data, indent=2)


def run_summary_cmd(
    diff: SchemaDiff,
    args: argparse.Namespace,
    out=None,
) -> int:
    if out is None:
        out = sys.stdout
    summary = summarize_diff(diff)
    if args.format == "json":
        print(_format_json(summary, getattr(args, "show_tables", False)), file=out)
    else:
        print(summary.as_text(), file=out)
        if getattr(args, "show_tables", False) and not summary.is_empty:
            print("", file=out)
            for t in summary.table_details:
                if t.has_changes:
                    status = "[+]" if t.added else "[-]" if t.removed else "[~]"
                    print(f"  {status} {t.name}", file=out)
    return 0 if summary.is_empty else 2
