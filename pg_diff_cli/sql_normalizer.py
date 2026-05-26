"""Normalize SQL statements for consistent comparison and formatting."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class NormalizeOptions:
    uppercase_keywords: bool = True
    strip_trailing_whitespace: bool = True
    collapse_whitespace: bool = True
    remove_inline_comments: bool = False


@dataclass
class NormalizeResult:
    original: str
    normalized: str
    changes: List[str] = field(default_factory=list)

    @property
    def was_changed(self) -> bool:
        return self.original != self.normalized


_SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
    "TABLE", "COLUMN", "INDEX", "CONSTRAINT", "ADD", "NOT", "NULL",
    "DEFAULT", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "UNIQUE",
    "IF", "EXISTS", "CASCADE", "RESTRICT", "SET", "TYPE", "FROM",
]

_KEYWORD_RE = re.compile(
    r'\b(' + '|'.join(_SQL_KEYWORDS) + r')\b',
    re.IGNORECASE,
)
_INLINE_COMMENT_RE = re.compile(r'--[^\n]*')
_MULTI_SPACE_RE = re.compile(r'[ \t]+')


def normalize_sql(sql: str, options: NormalizeOptions | None = None) -> NormalizeResult:
    """Normalize a single SQL statement according to the given options."""
    if options is None:
        options = NormalizeOptions()

    result = sql
    changes: List[str] = []

    if options.remove_inline_comments:
        cleaned = _INLINE_COMMENT_RE.sub('', result)
        if cleaned != result:
            changes.append("removed inline comments")
        result = cleaned

    if options.uppercase_keywords:
        uppercased = _KEYWORD_RE.sub(lambda m: m.group(0).upper(), result)
        if uppercased != result:
            changes.append("uppercased keywords")
        result = uppercased

    if options.collapse_whitespace:
        collapsed = _MULTI_SPACE_RE.sub(' ', result)
        if collapsed != result:
            changes.append("collapsed whitespace")
        result = collapsed

    if options.strip_trailing_whitespace:
        lines = result.splitlines()
        stripped_lines = [line.rstrip() for line in lines]
        stripped = "\n".join(stripped_lines)
        if stripped != result:
            changes.append("stripped trailing whitespace")
        result = stripped

    return NormalizeResult(original=sql, normalized=result, changes=changes)


def normalize_statements(statements: List[str], options: NormalizeOptions | None = None) -> List[NormalizeResult]:
    """Normalize a list of SQL statements."""
    return [normalize_sql(s, options) for s in statements]
