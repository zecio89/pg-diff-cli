"""Lint rules for schema diffs — warn about potentially dangerous migrations."""

from dataclasses import dataclass, field
from typing import List

from pg_diff_cli.schema_differ import SchemaDiff, TableDiff, ColumnDiff


@dataclass
class LintWarning:
    level: str  # 'warning' or 'error'
    table: str
    column: str | None
    message: str

    def __str__(self) -> str:
        loc = self.table if self.column is None else f"{self.table}.{self.column}"
        return f"[{self.level.upper()}] {loc}: {self.message}"


@dataclass
class LintResult:
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(w.level == "error" for w in self.warnings)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def _lint_column(table_name: str, col: ColumnDiff) -> List[LintWarning]:
    issues: List[LintWarning] = []
    after = col.after

    if after is None:
        return issues

    # Warn when a new NOT NULL column lacks a default — risky on large tables
    if col.before is None and not after.nullable and after.default is None:
        issues.append(LintWarning(
            level="warning",
            table=table_name,
            column=after.name,
            message="New NOT NULL column has no DEFAULT — will fail on non-empty tables",
        ))

    # Warn on type changes (potentially destructive)
    if col.before is not None and col.before.data_type != after.data_type:
        issues.append(LintWarning(
            level="warning",
            table=table_name,
            column=after.name,
            message=(
                f"Column type changed from '{col.before.data_type}' to '{after.data_type}' "
                "— ensure implicit cast exists"
            ),
        ))

    return issues


def _lint_table(table: TableDiff) -> List[LintWarning]:
    issues: List[LintWarning] = []

    # Dropping a table is always an error-level concern
    if table.removed:
        issues.append(LintWarning(
            level="error",
            table=table.table_name,
            column=None,
            message="Table is being dropped — this is irreversible",
        ))
        return issues

    for col in table.column_diffs:
        if col.removed:
            issues.append(LintWarning(
                level="error",
                table=table.table_name,
                column=col.column_name,
                message="Column is being dropped — data will be lost",
            ))
        else:
            issues.extend(_lint_column(table.table_name, col))

    return issues


def lint_diff(diff: SchemaDiff) -> LintResult:
    """Run all lint rules against a SchemaDiff and return a LintResult."""
    result = LintResult()
    for table in diff.table_diffs:
        result.warnings.extend(_lint_table(table))
    return result
