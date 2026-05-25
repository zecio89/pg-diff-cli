"""CLI sub-commands for schema hashing (hash, compare)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from pg_diff_cli.schema_hasher import hash_schema, diff_hashes, SchemaHash
from pg_diff_cli.snapshot import schema_from_dict, load_snapshot


def build_hash_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Compute and compare schema hashes."
    if parent is not None:
        parser = parent.add_parser("hash", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="pg-diff hash", description=desc)

    sub = parser.add_subparsers(dest="hash_cmd", required=True)

    compute = sub.add_parser("compute", help="Hash a snapshot file and print the digest.")
    compute.add_argument("snapshot", help="Path to a snapshot JSON file.")
    compute.add_argument("--json", dest="as_json", action="store_true",
                         help="Output full per-table hash map as JSON.")

    compare = sub.add_parser("compare", help="Compare hashes of two snapshot files.")
    compare.add_argument("source", help="Source snapshot JSON file.")
    compare.add_argument("target", help="Target snapshot JSON file.")

    return parser


def run_hash_cmd(args: argparse.Namespace) -> int:
    if args.hash_cmd == "compute":
        return _cmd_compute(args)
    if args.hash_cmd == "compare":
        return _cmd_compare(args)
    return 1


def _load(path: str) -> SchemaHash:
    snapshot = load_snapshot(path)
    if snapshot is None:
        print(f"Error: cannot read snapshot '{path}'", file=sys.stderr)
        sys.exit(1)
    return hash_schema(snapshot)


def _cmd_compute(args: argparse.Namespace) -> int:
    h = _load(args.snapshot)
    if args.as_json:
        print(json.dumps({"overall": h.overall, "tables": h.tables}, indent=2))
    else:
        print(h.overall)
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    src = _load(args.source)
    tgt = _load(args.target)
    changed = diff_hashes(src, tgt)
    if changed is None:
        print("Schemas are identical (hashes match).")
        return 0
    print(f"Schemas differ. {len(changed)} table(s) changed:")
    for name in changed:
        src_h = src.tables.get(name, "<absent>")
        tgt_h = tgt.tables.get(name, "<absent>")
        print(f"  {name}: {src_h[:12]}... -> {tgt_h[:12]}...")
    return 2
