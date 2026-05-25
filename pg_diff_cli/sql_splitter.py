"""Utilities for splitting a SQL migration script into individual statements."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class SplitResult:
    """Result of splitting a SQL script."""

    statements: List[str] = field(default_factory=list)
    raw_count: int = 0  # number of non-empty chunks before filtering

    @property
    def count(self) -> int:
        return len(self.statements)

    def is_empty(self) -> bool:
        return self.count == 0


# Matches a dollar-quoted block, e.g. $$ ... $$ or $tag$ ... $tag$
_DOLLAR_QUOTE_RE = re.compile(r"(\$[^$]*\$).*?\1", re.DOTALL)
# Matches a standard single-quoted string literal
_SINGLE_QUOTE_RE = re.compile(r"'(?:[^']|'')*'", re.DOTALL)
# Matches a line comment
_LINE_COMMENT_RE = re.compile(r"--[^\n]*")
# Matches a block comment
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(sql: str) -> str:
    """Remove SQL comments while preserving string literals."""
    result: List[str] = []
    i = 0
    n = len(sql)
    while i < n:
        # Dollar-quoted string
        m = _DOLLAR_QUOTE_RE.match(sql, i)
        if m:
            result.append(m.group(0))
            i = m.end()
            continue
        # Single-quoted string
        m = _SINGLE_QUOTE_RE.match(sql, i)
        if m:
            result.append(m.group(0))
            i = m.end()
            continue
        # Line comment
        m = _LINE_COMMENT_RE.match(sql, i)
        if m:
            i = m.end()
            continue
        # Block comment
        m = _BLOCK_COMMENT_RE.match(sql, i)
        if m:
            i = m.end()
            continue
        result.append(sql[i])
        i += 1
    return "".join(result)


def split_sql(sql: str, *, strip_comments: bool = True) -> SplitResult:
    """Split *sql* into individual statements delimited by semicolons.

    Dollar-quoted bodies and string literals are treated as opaque so that
    semicolons inside them are not treated as statement terminators.

    Args:
        sql: Raw SQL text potentially containing multiple statements.
        strip_comments: When *True* (default) comments are removed before
            splitting so that a trailing ``--`` comment does not become part
            of the returned statement text.

    Returns:
        A :class:`SplitResult` with the individual statement strings.
    """
    working = _strip_comments(sql) if strip_comments else sql
    raw_parts = working.split(";")
    raw_count = len(raw_parts)
    statements = [p.strip() for p in raw_parts if p.strip()]
    return SplitResult(statements=statements, raw_count=raw_count)
