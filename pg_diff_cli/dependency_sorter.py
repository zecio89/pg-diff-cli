"""Sort migration statements by dependency order (e.g. FK constraints after tables)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class SortedStatements:
    """Result of dependency-aware statement sorting."""
    statements: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Regex patterns to classify statement types
_CREATE_TABLE_RE = re.compile(r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.\"]+)", re.IGNORECASE)
_ALTER_TABLE_RE = re.compile(r"^\s*ALTER\s+TABLE\s+(?:ONLY\s+)?([\w.\"]+)", re.IGNORECASE)
_DROP_TABLE_RE = re.compile(r"^\s*DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\w.\"]+)", re.IGNORECASE)
_ADD_COLUMN_RE = re.compile(r"ADD\s+COLUMN", re.IGNORECASE)
_ADD_CONSTRAINT_RE = re.compile(r"ADD\s+CONSTRAINT", re.IGNORECASE)
_DROP_COLUMN_RE = re.compile(r"DROP\s+COLUMN", re.IGNORECASE)
_DROP_CONSTRAINT_RE = re.compile(r"DROP\s+CONSTRAINT", re.IGNORECASE)


def _classify(statement: str) -> int:
    """Return a sort priority for a SQL statement (lower = earlier)."""
    if _DROP_CONSTRAINT_RE.search(statement):
        return 0
    if _DROP_COLUMN_RE.search(statement):
        return 1
    if _DROP_TABLE_RE.match(statement):
        return 2
    if _CREATE_TABLE_RE.match(statement):
        return 3
    if _ALTER_TABLE_RE.match(statement) and _ADD_COLUMN_RE.search(statement):
        return 4
    if _ALTER_TABLE_RE.match(statement) and _ADD_CONSTRAINT_RE.search(statement):
        return 6
    if _ALTER_TABLE_RE.match(statement):
        return 5
    return 7


def _extract_table(statement: str) -> str | None:
    """Extract the primary table name referenced by a statement."""
    for pattern in (_CREATE_TABLE_RE, _ALTER_TABLE_RE, _DROP_TABLE_RE):
        m = pattern.match(statement)
        if m:
            return m.group(1).strip('"').lower()
    return None


def sort_statements(statements: List[str]) -> SortedStatements:
    """Sort SQL statements into a safe execution order.

    DROP CONSTRAINT → DROP COLUMN → DROP TABLE → CREATE TABLE
    → ADD COLUMN → ALTER TABLE → ADD CONSTRAINT → other
    """
    if not statements:
        return SortedStatements()

    warnings: List[str] = []
    seen_tables: Set[str] = set()

    annotated = [(i, stmt, _classify(stmt)) for i, stmt in enumerate(statements)]
    annotated.sort(key=lambda x: (x[2], x[0]))

    sorted_stmts = []
    for _, stmt, priority in annotated:
        table = _extract_table(stmt)
        if priority == 6 and table and table not in seen_tables:
            warnings.append(
                f"ADD CONSTRAINT on '{table}' but no preceding CREATE TABLE found — "
                "ensure the table exists in the target database."
            )
        if table:
            seen_tables.add(table)
        sorted_stmts.append(stmt)

    return SortedStatements(statements=sorted_stmts, warnings=warnings)
