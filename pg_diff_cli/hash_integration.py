"""High-level helpers that combine schema fetching with hashing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.schema_hasher import SchemaHash, hash_schema, diff_hashes


@dataclass
class HashComparison:
    source_hash: SchemaHash
    target_hash: SchemaHash
    changed_tables: Optional[list[str]]  # None means identical

    @property
    def is_identical(self) -> bool:
        return self.changed_tables is None

    @property
    def summary(self) -> str:
        if self.is_identical:
            return "Schemas are identical."
        n = len(self.changed_tables)  # type: ignore[arg-type]
        return f"{n} table(s) differ: {', '.join(self.changed_tables)}"


def compare_schemas(
    source: DatabaseSchema,
    target: DatabaseSchema,
) -> HashComparison:
    """Hash both schemas and return a HashComparison."""
    src_hash = hash_schema(source)
    tgt_hash = hash_schema(target)
    changed = diff_hashes(src_hash, tgt_hash)
    return HashComparison(
        source_hash=src_hash,
        target_hash=tgt_hash,
        changed_tables=changed,
    )


def quick_check(
    source: DatabaseSchema,
    target: DatabaseSchema,
) -> bool:
    """Return True if the two schemas are identical (hash shortcut)."""
    return hash_schema(source).matches(hash_schema(target))


def hash_report(comparison: HashComparison) -> str:
    """Produce a human-readable hash report."""
    lines = [
        f"Source hash : {comparison.source_hash.overall}",
        f"Target hash : {comparison.target_hash.overall}",
        comparison.summary,
    ]
    if not comparison.is_identical:
        lines.append("Changed tables:")
        for name in comparison.changed_tables:  # type: ignore[union-attr]
            s = comparison.source_hash.tables.get(name, "<absent>")
            t = comparison.target_hash.tables.get(name, "<absent>")
            lines.append(f"  {name}: {s[:16]}... -> {t[:16]}...")
    return "\n".join(lines)
