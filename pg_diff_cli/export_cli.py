"""CLI sub-command: export  — dump a live schema to JSON/YAML/CSV."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pg_diff_cli.schema_exporter import ExportFormat, export_schema
from pg_diff_cli.snapshot import schema_from_dict, load_snapshot


def build_export_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="pg-diff export",
        description="Export a schema snapshot to JSON, YAML, or CSV.",
    )
    parser = (
        parent.add_parser("export", **kwargs)
        if parent
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("snapshot", help="Path to a .json snapshot file")
    parser.add_argument(
        "--format",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.JSON.value,
        dest="fmt",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write to file instead of stdout",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)",
    )
    return parser


def run_export_cmd(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"error: snapshot file not found: {snapshot_path}", file=sys.stderr)
        return 1

    schema = load_snapshot(snapshot_path)
    if schema is None:
        print(f"error: could not parse snapshot: {snapshot_path}", file=sys.stderr)
        return 1

    fmt = ExportFormat(args.fmt)
    result = export_schema(schema, fmt=fmt, indent=args.indent)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result.content, encoding="utf-8")
        print(f"Exported {len(result)} bytes to {out}")
    else:
        sys.stdout.write(result.content)

    return 0
