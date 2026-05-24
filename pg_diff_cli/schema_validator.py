"""Validates a DatabaseSchema for common structural issues before diffing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pg_diff_cli.schema_fetcher import DatabaseSchema


@dataclass
class ValidationIssue:
    table: str
    column: str | None
    message: str
    level: str  # 'error' | 'warning'

    def __str__(self) -> str:
        location = self.table
        if self.column:
            location = f"{self.table}.{self.column}"
        return f"[{self.level.upper()}] {location}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]


def validate_schema(schema: DatabaseSchema) -> ValidationResult:
    """Run structural validation checks on a fetched schema."""
    result = ValidationResult()

    for table_name, table in schema.tables.items():
        if not table.columns:
            result.issues.append(
                ValidationIssue(
                    table=table_name,
                    column=None,
                    message="table has no columns",
                    level="warning",
                )
            )

        seen_columns: set[str] = set()
        for col in table.columns:
            if col.name in seen_columns:
                result.issues.append(
                    ValidationIssue(
                        table=table_name,
                        column=col.name,
                        message="duplicate column name",
                        level="error",
                    )
                )
            seen_columns.add(col.name)

            if not col.data_type:
                result.issues.append(
                    ValidationIssue(
                        table=table_name,
                        column=col.name,
                        message="column has no data type",
                        level="error",
                    )
                )

    return result
