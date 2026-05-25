"""Tag SQL statements with risk levels and metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_HIGH_PATTERNS = (
    "DROP TABLE",
    "DROP COLUMN",
    "DROP SCHEMA",
    "TRUNCATE",
)

_MEDIUM_PATTERNS = (
    "ALTER COLUMN",
    "ALTER TABLE",
    "ADD CONSTRAINT",
    "DROP CONSTRAINT",
    "RENAME",
)


@dataclass
class TaggedStatement:
    sql: str
    risk: RiskLevel
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "none"
        return f"[{self.risk.value.upper()}] {self.sql.strip()} (tags: {tag_str})"


def _risk_for(sql: str) -> RiskLevel:
    upper = sql.upper()
    for pat in _HIGH_PATTERNS:
        if pat in upper:
            return RiskLevel.HIGH
    for pat in _MEDIUM_PATTERNS:
        if pat in upper:
            return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _tags_for(sql: str) -> List[str]:
    upper = sql.upper()
    tags: List[str] = []
    if "DROP" in upper:
        tags.append("destructive")
    if "CREATE" in upper:
        tags.append("additive")
    if "NOT NULL" in upper:
        tags.append("constraint")
    if "DEFAULT" in upper:
        tags.append("default")
    return tags


def tag_statements(sql_statements: List[str]) -> List[TaggedStatement]:
    """Return a TaggedStatement for each SQL string."""
    return [
        TaggedStatement(sql=s, risk=_risk_for(s), tags=_tags_for(s))
        for s in sql_statements
        if s.strip()
    ]


def filter_by_risk(
    tagged: List[TaggedStatement], min_risk: RiskLevel
) -> List[TaggedStatement]:
    """Return only statements at or above *min_risk*."""
    order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
    threshold = order.index(min_risk)
    return [t for t in tagged if order.index(t.risk) >= threshold]
