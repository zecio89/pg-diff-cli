"""Audit log: record diff runs to a local JSONL file for history tracking."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_LOG_PATH = Path.home() / ".pg_diff_cli" / "audit.jsonl"


@dataclass
class AuditEntry:
    timestamp: str
    source_dsn: str
    target_dsn: str
    tables_added: int
    tables_removed: int
    tables_modified: int
    had_changes: bool
    output_file: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "source_dsn": self.source_dsn,
            "target_dsn": self.target_dsn,
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "tables_modified": self.tables_modified,
            "had_changes": self.had_changes,
            "output_file": self.output_file,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditEntry":
        return AuditEntry(
            timestamp=d["timestamp"],
            source_dsn=d["source_dsn"],
            target_dsn=d["target_dsn"],
            tables_added=d["tables_added"],
            tables_removed=d["tables_removed"],
            tables_modified=d["tables_modified"],
            had_changes=d["had_changes"],
            output_file=d.get("output_file"),
            tags=d.get("tags", []),
        )


def _redact_dsn(dsn: str) -> str:
    """Remove password from DSN for safe logging."""
    import re
    return re.sub(r"(://[^:@]*:)[^@]+(@)", r"\1***\2", dsn)


def build_entry(source_dsn: str, target_dsn: str, diff, output_file: Optional[str] = None, tags: Optional[List[str]] = None) -> AuditEntry:
    """Construct an AuditEntry from a SchemaDiff result."""
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_dsn=_redact_dsn(source_dsn),
        target_dsn=_redact_dsn(target_dsn),
        tables_added=len(diff.added_tables),
        tables_removed=len(diff.removed_tables),
        tables_modified=len(diff.modified_tables),
        had_changes=bool(diff.added_tables or diff.removed_tables or diff.modified_tables),
        output_file=output_file,
        tags=tags or [],
    )


def append_entry(entry: AuditEntry, log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> None:
    """Append a single audit entry to the JSONL log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")


def load_entries(log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> List[AuditEntry]:
    """Load all audit entries from the JSONL log file."""
    if not log_path.exists():
        return []
    entries = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries
