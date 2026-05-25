"""Compute stable hashes for schema objects to detect drift quickly."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema


@dataclass
class SchemaHash:
    """Holds per-table and overall schema hashes."""

    overall: str
    tables: Dict[str, str]

    def matches(self, other: "SchemaHash") -> bool:
        return self.overall == other.overall

    def changed_tables(self, other: "SchemaHash") -> list[str]:
        """Return table names whose hash differs between self and other."""
        all_keys = set(self.tables) | set(other.tables)
        return [
            k for k in sorted(all_keys)
            if self.tables.get(k) != other.tables.get(k)
        ]


def _stable_table_dict(table: TableSchema) -> dict:
    return {
        "name": table.name,
        "columns": [
            {
                "name": c.name,
                "data_type": c.data_type,
                "is_nullable": c.is_nullable,
                "default": c.default,
            }
            for c in sorted(table.columns, key=lambda c: c.name)
        ],
    }


def hash_table(table: TableSchema) -> str:
    """Return a hex SHA-256 digest for a single table."""
    payload = json.dumps(_stable_table_dict(table), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def hash_schema(schema: DatabaseSchema) -> SchemaHash:
    """Return a SchemaHash for the entire database schema."""
    table_hashes: Dict[str, str] = {
        name: hash_table(table)
        for name, table in sorted(schema.tables.items())
    }
    combined = json.dumps(table_hashes, sort_keys=True, ensure_ascii=True)
    overall = hashlib.sha256(combined.encode()).hexdigest()
    return SchemaHash(overall=overall, tables=table_hashes)


def diff_hashes(source: SchemaHash, target: SchemaHash) -> Optional[list[str]]:
    """Return list of changed table names, or None if schemas are identical."""
    if source.matches(target):
        return None
    return source.changed_tables(target)
