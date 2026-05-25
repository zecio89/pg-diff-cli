"""CLI helpers for the schema-annotator feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from pg_diff_cli.schema_annotator import AnnotatedSchema, TableAnnotation, annotate_diff
from pg_diff_cli.snapshot import load_snapshot
from pg_diff_cli.schema_differ import diff_schemas


def build_annotator_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Manage schema annotations (human notes attached to tables/columns)."
    if parent is not None:
        p = parent.add_parser("annotate", help=desc)
    else:
        p = argparse.ArgumentParser(prog="pg-annotate", description=desc)

    sub = p.add_subparsers(dest="ann_cmd", required=True)

    add_p = sub.add_parser("add", help="Add an annotation")
    add_p.add_argument("--file", required=True, help="Annotation JSON file")
    add_p.add_argument("--table", required=True)
    add_p.add_argument("--column", default=None)
    add_p.add_argument("--note", required=True)

    show_p = sub.add_parser("show", help="Show annotations for a snapshot diff")
    show_p.add_argument("--source", required=True, help="Source snapshot file")
    show_p.add_argument("--target", required=True, help="Target snapshot file")
    show_p.add_argument("--file", required=True, help="Annotation JSON file")

    return p


def _load_annotations(path: str) -> AnnotatedSchema:
    from pg_diff_cli.schema_fetcher import DatabaseSchema
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text())
        schema = DatabaseSchema(tables={})
        ann = AnnotatedSchema(schema=schema)
        for table, info in data.items():
            ann.table_annotations[table] = TableAnnotation(
                table=table,
                note=info.get("note", ""),
                column_notes=info.get("columns", {}),
            )
        return ann
    from pg_diff_cli.schema_fetcher import DatabaseSchema
    return AnnotatedSchema(schema=DatabaseSchema(tables={}))


def _save_annotations(ann: AnnotatedSchema, path: str) -> None:
    data = {}
    for table, info in ann.table_annotations.items():
        data[table] = {"note": info.note, "columns": info.column_notes}
    Path(path).write_text(json.dumps(data, indent=2))


def run_annotator_cmd(args: argparse.Namespace) -> int:
    if args.ann_cmd == "add":
        ann = _load_annotations(args.file)
        if args.column:
            ann.annotate_column(args.table, args.column, args.note)
        else:
            ann.annotate_table(args.table, args.note)
        _save_annotations(ann, args.file)
        print(f"Annotation saved to {args.file}")
        return 0

    if args.ann_cmd == "show":
        src = load_snapshot(args.source)
        tgt = load_snapshot(args.target)
        diff = diff_schemas(src, tgt)
        ann = _load_annotations(args.file)
        lines = annotate_diff(diff, ann)
        if lines:
            print("\n".join(lines))
        else:
            print("-- No annotations for affected tables.")
        return 0

    print(f"Unknown subcommand: {args.ann_cmd}", file=sys.stderr)
    return 1
