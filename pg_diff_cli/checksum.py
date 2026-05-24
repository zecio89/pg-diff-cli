"""Schema checksum utilities for detecting changes without a full diff."""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema
from pg_diff_cli.snapshot import schema_to_dict


def _stable_json(obj: object) -> str:
    """Serialize *obj* to JSON with sorted keys for deterministic output."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def checksum_table(table: TableSchema) -> str:
    """Return a hex MD5 digest representing a single table's structure."""
    columns_repr = [
        {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
        for c in sorted(table.columns, key=lambda c: c.name)
    ]
    payload = _stable_json({"table": table.name, "columns": columns_repr})
    return hashlib.md5(payload.encode()).hexdigest()


def checksum_schema(schema: DatabaseSchema) -> str:
    """Return a hex SHA-256 digest representing the entire database schema.

    The digest is computed over a stable JSON serialisation so that two
    schemas with identical structure always produce the same checksum,
    regardless of the order in which tables were fetched.
    """
    table_checksums = {
        name: checksum_table(table)
        for name, table in sorted(schema.tables.items())
    }
    payload = _stable_json(table_checksums)
    return hashlib.sha256(payload.encode()).hexdigest()


def checksums_match(
    schema_a: DatabaseSchema,
    schema_b: DatabaseSchema,
) -> bool:
    """Return *True* when both schemas produce identical checksums."""
    return checksum_schema(schema_a) == checksum_schema(schema_b)


def checksum_report(
    source: DatabaseSchema,
    target: DatabaseSchema,
    source_label: str = "source",
    target_label: str = "target",
) -> str:
    """Return a human-readable string summarising the checksum comparison."""
    src_hex = checksum_schema(source)
    tgt_hex = checksum_schema(target)
    match_str = "MATCH" if src_hex == tgt_hex else "MISMATCH"
    lines = [
        f"Schema checksum comparison: {match_str}",
        f"  {source_label}: {src_hex}",
        f"  {target_label}: {tgt_hex}",
    ]
    return "\n".join(lines)
