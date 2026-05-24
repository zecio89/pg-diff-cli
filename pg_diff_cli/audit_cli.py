"""CLI sub-commands for the audit log: list and clear."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from pg_diff_cli.audit_log import DEFAULT_AUDIT_LOG_PATH, AuditEntry, load_entries


def build_audit_parser(subparsers) -> None:
    """Register 'audit' sub-command with list / clear actions."""
    audit_p = subparsers.add_parser("audit", help="Manage the diff audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    list_p = audit_sub.add_parser("list", help="Show recent audit entries")
    list_p.add_argument("--log", default=str(DEFAULT_AUDIT_LOG_PATH), help="Path to audit log file")
    list_p.add_argument("--limit", type=int, default=20, help="Maximum entries to show (default: 20)")
    list_p.add_argument("--changed-only", action="store_true", help="Only show runs that produced changes")

    clear_p = audit_sub.add_parser("clear", help="Delete the audit log file")
    clear_p.add_argument("--log", default=str(DEFAULT_AUDIT_LOG_PATH), help="Path to audit log file")
    clear_p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")


def _format_entry(entry: AuditEntry) -> str:
    changed = "CHANGED" if entry.had_changes else "no-op"
    parts = [
        f"  [{entry.timestamp}] {changed}",
        f"    src : {entry.source_dsn}",
        f"    tgt : {entry.target_dsn}",
        f"    +{entry.tables_added} added  -{entry.tables_removed} removed  ~{entry.tables_modified} modified",
    ]
    if entry.output_file:
        parts.append(f"    out : {entry.output_file}")
    if entry.tags:
        parts.append(f"    tags: {', '.join(entry.tags)}")
    return "\n".join(parts)


def run_audit_cmd(args: argparse.Namespace) -> int:
    log_path = Path(args.log)

    if args.audit_cmd == "list":
        entries = load_entries(log_path)
        if args.changed_only:
            entries = [e for e in entries if e.had_changes]
        entries = entries[-args.limit:]
        if not entries:
            print("No audit entries found.")
            return 0
        print(f"Showing {len(entries)} audit log entr{'y' if len(entries) == 1 else 'ies'}:\n")
        for entry in entries:
            print(_format_entry(entry))
            print()
        return 0

    if args.audit_cmd == "clear":
        if not log_path.exists():
            print("Audit log does not exist.")
            return 0
        if not args.yes:
            answer = input(f"Delete {log_path}? [y/N] ").strip().lower()
            if answer != "y":
                print("Aborted.")
                return 1
        log_path.unlink()
        print(f"Audit log deleted: {log_path}")
        return 0

    print(f"Unknown audit sub-command: {args.audit_cmd}", file=sys.stderr)
    return 1
