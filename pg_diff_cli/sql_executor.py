"""Dry-run and live SQL execution support for migration statements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExecutionResult:
    statements_run: int = 0
    statements_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        mode = "(dry-run) " if self.dry_run else ""
        return (
            f"{mode}{self.statements_run} executed, "
            f"{self.statements_skipped} skipped, "
            f"{len(self.errors)} error(s)"
        )


def execute_sql(
    dsn: str,
    statements: List[str],
    dry_run: bool = False,
    stop_on_error: bool = True,
) -> ExecutionResult:
    """Execute a list of SQL statements against *dsn*.

    When *dry_run* is True the statements are validated but not committed.
    """
    result = ExecutionResult(dry_run=dry_run)

    if not statements:
        return result

    try:
        import psycopg2  # type: ignore
    except ImportError:
        result.errors.append("psycopg2 is not installed")
        return result

    conn: Optional[object] = None
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        cur = conn.cursor()
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                result.statements_skipped += 1
                continue
            try:
                cur.execute(stmt)
                result.statements_run += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(str(exc))
                if stop_on_error:
                    conn.rollback()
                    return result
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        result.errors.append(str(exc))
    finally:
        if conn is not None:
            conn.close()

    return result
