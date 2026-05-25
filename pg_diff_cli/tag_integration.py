"""Integrate statement tagging into the diff/migration pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .migration_generator import generate_migration
from .schema_differ import SchemaDiff
from .statement_tagger import RiskLevel, TaggedStatement, tag_statements


@dataclass
class TaggedMigration:
    tagged: List[TaggedStatement]

    @property
    def risk_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {r.value: 0 for r in RiskLevel}
        for t in self.tagged:
            counts[t.risk.value] += 1
        return counts

    @property
    def has_high_risk(self) -> bool:
        return any(t.risk is RiskLevel.HIGH for t in self.tagged)

    @property
    def sql_statements(self) -> List[str]:
        return [t.sql for t in self.tagged]


def tag_migration_from_diff(diff: SchemaDiff) -> TaggedMigration:
    """Generate migration SQL from *diff* and annotate each statement."""
    raw_sql = generate_migration(diff)
    statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
    # Strip leading comment-only lines that are not real SQL
    real = [s for s in statements if not s.startswith("--")]
    tagged = tag_statements(real)
    return TaggedMigration(tagged=tagged)


def risk_gate(migration: TaggedMigration, allow_high: bool = False) -> bool:
    """Return True when the migration may proceed.

    If *allow_high* is False and any HIGH-risk statement exists, returns False.
    """
    if migration.has_high_risk and not allow_high:
        return False
    return True
